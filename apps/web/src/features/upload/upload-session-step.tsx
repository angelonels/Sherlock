"use client";

import type { ApiClient } from "@/lib/api-client";
import { DatasetPreviewTab, DatasetQualityTab, DatasetSchemaTab } from "@/features/datasets/dataset-tabs";
import type { Dataset, DatasetColumn, DatasetQualityIssue, UploadSession } from "@/lib/types";
import { useMutation } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { AlertTriangle, FileSpreadsheet, Loader2, Play, Trash2, Upload } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

type UploadSessionStepProps = {
  apiClient: ApiClient;
  onDatasetReady?: (datasetId: string) => void;
};

const datasetNameSchema = z.object({
  datasetName: z.string().trim().min(1, "Dataset name is required.").max(120, "Dataset name must be 120 characters or fewer."),
});
type DatasetNameForm = z.infer<typeof datasetNameSchema>;

function formatBytes(value: number): string {
  if (value < 1024) {
    return `${value} B`;
  }
  if (value < 1024 * 1024) {
    return `${(value / 1024).toFixed(1)} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadSessionStep({ apiClient, onDatasetReady }: UploadSessionStepProps) {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploadSession, setUploadSession] = useState<UploadSession | null>(null);
  const [dataset, setDataset] = useState<Dataset | null>(null);
  const [previewRows, setPreviewRows] = useState<Record<string, unknown>[]>([]);
  const [previewCursor, setPreviewCursor] = useState<string | null>(null);
  const [datasetColumns, setDatasetColumns] = useState<DatasetColumn[]>([]);
  const [qualityIssues, setQualityIssues] = useState<DatasetQualityIssue[]>([]);
  const [activeReviewTab, setActiveReviewTab] = useState<"preview" | "schema" | "quality">("preview");
  const [isLoadingNextPreview, setIsLoadingNextPreview] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors: formErrors, isValid: isDatasetNameValid },
  } = useForm<DatasetNameForm>({
    resolver: zodResolver(datasetNameSchema),
    defaultValues: { datasetName: "" },
    mode: "onChange",
  });
  const uploadMutation = useMutation({
    mutationFn: (file: File) => apiClient.createUploadSession(file),
  });
  const sheetMutation = useMutation({
    mutationFn: ({ uploadSessionId, sheetName }: { uploadSessionId: string; sheetName: string }) =>
      apiClient.updateUploadSessionSheet(uploadSessionId, sheetName),
  });
  const deleteUploadMutation = useMutation({
    mutationFn: (uploadSessionId: string) => apiClient.deleteUploadSession(uploadSessionId),
  });
  const createDatasetMutation = useMutation({
    mutationFn: (payload: { upload_session_id: string; name: string; selected_sheet_name?: string | null }) =>
      apiClient.createDataset(payload),
  });
  const createChatMutation = useMutation({
    mutationFn: (datasetId: string) => apiClient.createChat(datasetId),
  });
  const isUploading = uploadMutation.isPending || sheetMutation.isPending;
  const isCreatingDataset = createDatasetMutation.isPending;
  const isDeleting = deleteUploadMutation.isPending;

  async function handleFile(file: File | undefined) {
    if (!file) {
      return;
    }

    setError(null);
    try {
      const createdUpload = await uploadMutation.mutateAsync(file);
      setUploadSession(createdUpload);
      sessionStorage.setItem("sherlock.uploadSessionId", createdUpload.id);
      sessionStorage.removeItem("sherlock.datasetId");
      setValue("datasetName", file.name.replace(/\.[^.]+$/, ""), { shouldValidate: true });
      setDataset(null);
      setPreviewRows([]);
    } catch (uploadError) {
      setError(uploadError instanceof Error ? uploadError.message : "Upload inspection failed.");
    }
  }

  async function selectSheet(sheetName: string) {
    if (!uploadSession) {
      return;
    }
    setError(null);
    try {
      setUploadSession(await sheetMutation.mutateAsync({ uploadSessionId: uploadSession.id, sheetName }));
    } catch (sheetError) {
      setError(sheetError instanceof Error ? sheetError.message : "Sheet inspection failed.");
    }
  }

  async function cancelUpload() {
    if (!uploadSession) {
      return;
    }
    try {
      await deleteUploadMutation.mutateAsync(uploadSession.id);
      setUploadSession(null);
      setDataset(null);
      setPreviewRows([]);
      sessionStorage.removeItem("sherlock.uploadSessionId");
      sessionStorage.removeItem("sherlock.datasetId");
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "Upload cancellation failed.");
    }
  }

  const loadDatasetReview = useCallback(async (datasetId: string) => {
    const [preview, columns, issues] = await Promise.all([
      apiClient.getDatasetPreview(datasetId),
      apiClient.getDatasetColumns(datasetId),
      apiClient.getDatasetQualityIssues(datasetId),
    ]);
    setPreviewRows(preview.data);
    setPreviewCursor(preview.pagination.next_cursor);
    setDatasetColumns(columns.data);
    setQualityIssues(issues.data);
  }, [apiClient]);

  const pollDataset = useCallback(async (datasetId: string) => {
    for (let index = 0; index < 120; index += 1) {
      const nextDataset = await apiClient.getDataset(datasetId);
      setDataset(nextDataset);
      if (nextDataset.status === "ready" || nextDataset.status === "locked") {
        await loadDatasetReview(datasetId);
        onDatasetReady?.(datasetId);
        return;
      }
      if (nextDataset.status === "failed") {
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    setError("Ingestion is taking longer than expected. Refresh this page to recover its latest state.");
  }, [apiClient, loadDatasetReview, onDatasetReady]);

  useEffect(() => {
    const uploadSessionId = sessionStorage.getItem("sherlock.uploadSessionId");
    const datasetId = sessionStorage.getItem("sherlock.datasetId");
    if (!uploadSessionId && !datasetId) {
      return;
    }

    let cancelled = false;
    async function restoreDurableState() {
      try {
        if (uploadSessionId) {
          const restoredUpload = await apiClient.getUploadSession(uploadSessionId);
          if (!cancelled) {
            setUploadSession(restoredUpload);
            setValue("datasetName", restoredUpload.original_filename.replace(/\.[^.]+$/, ""), { shouldValidate: true });
          }
        }
        if (datasetId) {
          const restoredDataset = await apiClient.getDataset(datasetId);
          if (!cancelled) {
            setDataset(restoredDataset);
            if (restoredDataset.status === "ready" || restoredDataset.status === "locked") {
              await loadDatasetReview(datasetId);
              onDatasetReady?.(datasetId);
            } else if (restoredDataset.status === "processing") {
              await pollDataset(datasetId);
            }
          }
        }
      } catch {
        sessionStorage.removeItem("sherlock.uploadSessionId");
        sessionStorage.removeItem("sherlock.datasetId");
        if (!cancelled) {
          setError("The previous upload state could not be restored. Start a new upload.");
        }
      }
    }

    void restoreDurableState();
    return () => {
      cancelled = true;
    };
  }, [apiClient, loadDatasetReview, onDatasetReady, pollDataset, setValue]);

  async function createDataset(values: DatasetNameForm) {
    if (!uploadSession) {
      return;
    }
    setError(null);
    try {
      const created = await createDatasetMutation.mutateAsync({
        upload_session_id: uploadSession.id,
        name: values.datasetName.trim(),
        selected_sheet_name: uploadSession.selected_sheet_name,
      });
      setDataset(created);
      sessionStorage.setItem("sherlock.datasetId", created.id);
      await pollDataset(created.id);
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : "Dataset creation failed.");
    }
  }

  async function loadNextPreviewRows() {
    if (!dataset || !previewCursor) {
      return;
    }
    setIsLoadingNextPreview(true);
    setError(null);
    try {
      const next = await apiClient.getDatasetPreview(dataset.id, previewCursor);
      setPreviewRows((rows) => [...rows, ...next.data]);
      setPreviewCursor(next.pagination.next_cursor);
    } catch (previewError) {
      setError(previewError instanceof Error ? previewError.message : "More preview rows could not be loaded.");
    } finally {
      setIsLoadingNextPreview(false);
    }
  }

  async function startInvestigation() {
    if (!dataset) {
      return;
    }
    setError(null);
    try {
      const chat = await createChatMutation.mutateAsync(dataset.id);
      sessionStorage.removeItem("sherlock.uploadSessionId");
      sessionStorage.removeItem("sherlock.datasetId");
      router.push(`/app/chat/${chat.id}`);
    } catch (chatError) {
      setError(chatError instanceof Error ? chatError.message : "Investigation could not be started.");
    }
  }

  const columns = uploadSession?.preview_rows[0] ? Object.keys(uploadSession.preview_rows[0]) : [];

  return (
    <section className="mx-auto flex w-full max-w-5xl flex-col gap-5 py-6">
      <div className="border border-[#d9cdbf] bg-[#fffaf7] p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-[#8f6a4e]">Upload session</p>
            <h2 className="mt-2 text-xl font-semibold tracking-[-0.04em]">Inspect a CSV or XLSX file</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[#655c52]">
              Supports CSV and XLSX files up to 25 MB, 100 columns, and 100 preview rows before dataset creation.
            </p>
          </div>
          {uploadSession ? (
            <button
              type="button"
              onClick={cancelUpload}
              disabled={isDeleting}
              className="inline-flex h-10 items-center justify-center gap-2 border border-[#d9cdbf] bg-[#fffaf7] px-3 text-sm font-semibold text-[#51473f] disabled:opacity-60"
            >
              <Trash2 size={16} />
              Cancel
            </button>
          ) : null}
        </div>

        <label
          className="mt-5 flex min-h-40 cursor-pointer flex-col items-center justify-center gap-3 border border-dashed border-[#b8aa9a] bg-[#fbf7f1] px-5 py-8 text-center"
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();
            void handleFile(event.dataTransfer.files[0]);
          }}
        >
          {isUploading ? <Loader2 className="animate-spin" size={24} /> : <Upload size={24} />}
          <span className="text-sm font-semibold text-[#51473f]">
            {isUploading ? "Inspecting upload" : "Choose a file or drop it here"}
          </span>
          <span className="text-xs text-[#655c52]">CSV, XLSX. Empty files, macro workbooks, and headers-only files are rejected.</span>
          <input
            ref={inputRef}
            aria-label="Upload CSV or XLSX file"
            className="sr-only"
            type="file"
            accept=".csv,.xlsx"
            onChange={(event) => void handleFile(event.target.files?.[0])}
          />
        </label>

        {error ? (
          <p className="mt-4 border border-[#b84b3c] bg-[#fff2ef] px-3 py-2 text-sm text-[#7d2f26]" role="alert">
            {error}
          </p>
        ) : null}
      </div>

      {uploadSession ? (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_18rem]">
          <section className="min-w-0 border border-[#d9cdbf] bg-[#fffaf7] p-5">
            <div className="flex flex-wrap items-center gap-3 text-sm text-[#655c52]">
              <FileSpreadsheet size={17} />
              <span className="font-semibold text-[#51473f]">{uploadSession.original_filename}</span>
              <span>{formatBytes(uploadSession.file_size_bytes)}</span>
              <span>{uploadSession.status}</span>
            </div>

            {uploadSession.sheet_names && uploadSession.sheet_names.length > 1 ? (
              <label className="mt-4 block text-sm font-semibold text-[#51473f]">
                Sheet
                <select
                  className="mt-2 h-10 w-full border border-[#d9cdbf] bg-[#fbf7f1] px-3 text-sm"
                  value={uploadSession.selected_sheet_name ?? uploadSession.recommended_sheet_name ?? uploadSession.sheet_names[0]}
                  onChange={(event) => void selectSheet(event.target.value)}
                >
                  {uploadSession.sheet_names.map((sheetName) => (
                    <option key={sheetName} value={sheetName}>
                      {sheetName}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}

            <div className="mt-5 overflow-x-auto">
              <table className="w-full min-w-[36rem] border-collapse text-left text-sm">
                <thead>
                  <tr>
                    {columns.map((column) => (
                      <th key={column} className="border-b border-[#d9cdbf] px-3 py-2 font-semibold text-[#51473f]">
                        {column}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {uploadSession.preview_rows.map((row, rowIndex) => (
                    <tr key={rowIndex} className="border-b border-[#eee4d8]">
                      {columns.map((column) => (
                        <td key={column} className="max-w-72 truncate px-3 py-2 text-[#655c52]">
                          {String(row[column] ?? "")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <aside className="space-y-5">
            <form
              className="border border-[#d9cdbf] bg-[#fffaf7] p-4"
              onSubmit={handleSubmit((values) => void createDataset(values))}
            >
              <label className="block text-sm font-semibold text-[#51473f]">
                Dataset name
                <input
                  className="mt-2 h-10 w-full border border-[#d9cdbf] bg-[#fbf7f1] px-3 text-sm"
                  {...register("datasetName")}
                />
              </label>
              {formErrors.datasetName ? (
                <p className="mt-2 text-xs text-[#7d2f26]" role="alert">{formErrors.datasetName.message}</p>
              ) : null}
              <button
                type="submit"
                disabled={isCreatingDataset || !isDatasetNameValid}
                className="mt-3 inline-flex h-10 w-full items-center justify-center gap-2 border border-[#241f1a] bg-[#241f1a] px-3 text-sm font-semibold text-[#fffaf7] disabled:opacity-60"
              >
                {isCreatingDataset ? <Loader2 className="animate-spin" size={16} /> : <FileSpreadsheet size={16} />}
                Create Dataset
              </button>
              {dataset ? (
                <p className="mt-3 text-sm text-[#655c52]">
                  Dataset status: <span className="font-semibold">{dataset.status}</span>
                  {dataset.ingestion_error ? ` (${dataset.ingestion_error})` : ""}
                </p>
              ) : null}
            </form>

            <section className="border border-[#d9cdbf] bg-[#fffaf7] p-4">
              <h3 className="text-sm font-semibold text-[#51473f]">Detected columns</h3>
              <div className="mt-3 space-y-2">
                {uploadSession.detected_columns.map((column) => (
                  <div key={column.clean_name} className="border border-[#eee4d8] bg-[#fbf7f1] px-3 py-2 text-sm">
                    <div className="font-medium text-[#51473f]">{column.original_name}</div>
                    <div className="text-xs text-[#655c52]">{column.clean_name} · {column.inferred_type}</div>
                  </div>
                ))}
              </div>
            </section>

            <section className="border border-[#d9cdbf] bg-[#fffaf7] p-4">
              <h3 className="text-sm font-semibold text-[#51473f]">Warnings</h3>
              <div className="mt-3 space-y-2">
                {uploadSession.warnings.length === 0 ? (
                  <p className="text-sm text-[#655c52]">No upload warnings.</p>
                ) : (
                  uploadSession.warnings.map((warning) => (
                    <div key={`${warning.code}-${warning.message}`} className="flex gap-2 border border-[#eee4d8] bg-[#fbf7f1] px-3 py-2 text-sm text-[#655c52]">
                      <AlertTriangle className="mt-0.5 shrink-0" size={15} />
                      <span>{warning.message}</span>
                    </div>
                  ))
                )}
              </div>
            </section>
          </aside>
        </div>
      ) : null}

      {dataset && (dataset.status === "ready" || dataset.status === "locked") ? (
        <section className="border border-[#d9cdbf] bg-[#fffaf7] p-5">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-[#8f6a4e]">Dataset review</p>
              <h2 className="mt-2 text-xl font-semibold tracking-[-0.04em]">{dataset.name}</h2>
              <p className="mt-2 text-sm text-[#655c52]">
                {dataset.row_count} rows · {dataset.column_count} columns · quality {dataset.quality_status ?? "unknown"}
              </p>
            </div>
            <button
              type="button"
              onClick={() => void startInvestigation()}
              disabled={createChatMutation.isPending}
              className="inline-flex h-10 items-center justify-center gap-2 border border-[#241f1a] bg-[#241f1a] px-3 text-sm font-semibold text-[#fffaf7] disabled:opacity-60"
            >
              {createChatMutation.isPending ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} />}
              Start Investigation
            </button>
          </div>
          <div className="mt-5 flex flex-wrap gap-2">
            {(["preview", "schema", "quality"] as const).map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setActiveReviewTab(tab)}
                className={[
                  "border px-3 py-2 text-sm font-semibold",
                  activeReviewTab === tab ? "border-[#241f1a] bg-[#241f1a] text-[#fffaf7]" : "border-[#d9cdbf] bg-[#fbf7f1] text-[#51473f]",
                ].join(" ")}
              >
                {tab}
              </button>
            ))}
          </div>
          <div className="mt-4">
            {activeReviewTab === "preview" ? (
              <DatasetPreviewTab
                rows={previewRows}
                hasNextPage={Boolean(previewCursor)}
                isLoadingNext={isLoadingNextPreview}
                onLoadNext={() => void loadNextPreviewRows()}
              />
            ) : null}
            {activeReviewTab === "schema" ? <DatasetSchemaTab columns={datasetColumns} /> : null}
            {activeReviewTab === "quality" ? <DatasetQualityTab issues={qualityIssues} /> : null}
          </div>
        </section>
      ) : null}
    </section>
  );
}
