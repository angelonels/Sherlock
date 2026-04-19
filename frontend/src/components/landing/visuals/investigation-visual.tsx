import { AnimatedNumber } from "@/components/landing/animated-number";
import { chartBars, sampleRows } from "@/components/landing/landing-content";
import { TiltSurface } from "@/components/landing/tilt-surface";
import {
  ChartLineUp,
  CheckCircle,
  FileCsv,
  Rows,
  Table,
  TextColumns,
  Warning,
} from "@phosphor-icons/react/dist/ssr";

export function InvestigationVisual() {
  return (
    <div
      className="analysis-grid relative min-h-[640px] overflow-hidden bg-[#eee6db] lg:min-h-full"
      aria-label="Sherlock product preview"
    >
      <div className="absolute inset-0 bg-[linear-gradient(rgba(94,78,60,0.11)_1px,transparent_1px),linear-gradient(90deg,rgba(94,78,60,0.11)_1px,transparent_1px)] bg-[size:32px_32px]" />
      <div className="fine-stripes absolute right-0 top-0 hidden h-32 w-32 opacity-50 lg:block" />
      <div className="absolute -right-28 top-16 h-72 w-72 rounded-full bg-[#d59a67]/25 blur-3xl" />
      <div className="absolute -bottom-24 left-12 h-72 w-72 rounded-full bg-[#a9b19d]/24 blur-3xl" />

      <div className="relative mx-4 my-8 grid gap-4 sm:mx-8 lg:mx-0 lg:my-0 lg:min-h-[760px]">
        <TiltSurface className="premium-surface mobile-polish-panel border-beam float-soft self-start border border-[#d3c5b6] bg-[#fffaf7]/94 p-4 sm:p-5 lg:absolute lg:left-0 lg:right-16 lg:top-16">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#e3d7ca] pb-4">
            <div>
              <p className="font-mono text-xs text-[#8f6a4e]">upload session</p>
              <h2 className="mt-1 text-xl font-semibold tracking-[-0.04em] text-[#241f1a]">
                sales_orders.xlsx
              </h2>
            </div>
            <div className="sheen inline-flex items-center gap-2 border border-[#e0d3c4] bg-[#f3eadf] px-3 py-2 text-sm font-medium text-[#5b5148]">
              <FileCsv size={17} weight="duotone" />
              CSV/XLSX
            </div>
          </div>

          <div className="grid gap-4 py-5 md:grid-cols-[0.82fr_1.18fr]">
            <div className="space-y-4">
              <div className="lift-card border border-[#e0d3c4] bg-[#f8f0e7] p-4">
                <p className="font-mono text-xs text-[#8f6a4e]">selected sheet</p>
                <p className="mt-3 text-3xl font-semibold tracking-[-0.055em] text-[#241f1a]">
                  Orders
                </p>
                <p className="mt-2 text-sm leading-6 text-[#6f655b]">
                  Pick the sheet, preview the data, then start asking focused questions.
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="border-t border-[#d3c5b6] pt-3">
                  <AnimatedNumber
                    value={11750}
                    className="block font-mono text-2xl tracking-[-0.04em] text-[#241f1a]"
                  />
                  <p className="mt-1 text-xs leading-4 text-[#756a60]">usable rows</p>
                </div>
                <div className="border-t border-[#d3c5b6] pt-3">
                  <AnimatedNumber
                    value={341}
                    className="block font-mono text-2xl tracking-[-0.04em] text-[#241f1a]"
                  />
                  <p className="mt-1 text-xs leading-4 text-[#756a60]">missing values</p>
                </div>
              </div>
            </div>

            <div className="premium-surface overflow-hidden border border-[#e0d3c4] bg-[#fffaf7]">
              <div className="grid grid-cols-[0.7fr_1fr_1fr_0.8fr] bg-[#eadfd2] px-3 py-2 font-mono text-[11px] text-[#675a50]">
                <span>month</span>
                <span>region</span>
                <span>revenue</span>
                <span>quality</span>
              </div>
              {sampleRows.map((row) => (
                <div
                  key={row.join("-")}
                  className="grid grid-cols-[0.7fr_1fr_1fr_0.8fr] border-t border-[#eadfd2] px-3 py-3 text-sm text-[#51473f] transition-colors duration-300 hover:bg-[#f8f0e7]"
                >
                  {row.map((cell) => (
                    <span key={cell} className="truncate">
                      {cell}
                    </span>
                  ))}
                </div>
              ))}
            </div>
          </div>
        </TiltSurface>

        <TiltSurface className="premium-dark-surface mobile-polish-panel border-beam float-soft-delayed self-end border border-[#322921] bg-[#241f1a] p-4 text-[#fffaf7] sm:p-5 lg:absolute lg:bottom-12 lg:left-16 lg:right-8 xl:left-24 xl:right-16">
          <div className="grid gap-4 lg:grid-cols-[0.9fr_1.1fr]">
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <span className="signal-pulse grid size-10 shrink-0 place-items-center bg-[#c98146] text-[#241f1a]">
                  <TextColumns size={21} weight="duotone" />
                </span>
                <div>
                  <p className="font-mono text-xs text-[#dfb48e]">assistant answer</p>
                  <h3 className="mt-1 text-2xl font-semibold tracking-[-0.055em]">
                    March led the quarter.
                  </h3>
                </div>
              </div>
              <p className="max-w-md text-sm leading-6 text-[#d9cdc0]">
                Sherlock returns findings with supporting blocks, quality context, and
                follow-up prompts for the next question.
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div className="lift-card border border-[#57483c] p-3">
                  <Rows size={20} className="text-[#c98146]" />
                  <AnimatedNumber value={250} className="mt-4 block font-mono text-2xl" />
                  <p className="mt-1 text-xs text-[#b9aa9a]">duplicates removed</p>
                </div>
                <div className="lift-card border border-[#57483c] p-3">
                  <Warning size={20} className="text-[#c98146]" />
                  <p className="mt-4 font-mono text-2xl">warning</p>
                  <p className="mt-1 text-xs text-[#b9aa9a]">quality status</p>
                </div>
              </div>
            </div>

            <div className="premium-dark-surface border border-[#57483c] bg-[#2f2821] p-4">
              <div className="mb-4 flex items-center justify-between">
                <p className="font-mono text-xs text-[#dfb48e]">chart block</p>
                <ChartLineUp size={21} className="text-[#c98146]" />
              </div>
              <div className="flex h-44 items-end gap-3 border-b border-l border-[#6a5749] px-3">
                {chartBars.map((bar) => (
                  <div key={bar.label} className="flex h-full flex-1 flex-col justify-end gap-2">
                    <div
                      className="bar-rise min-h-5 bg-[#c98146] shadow-[inset_0_1px_0_rgba(255,255,255,0.35)] transition-transform duration-500 hover:scale-y-105"
                      style={{ height: bar.height }}
                    />
                    <span className="pb-2 text-center font-mono text-[10px] text-[#b9aa9a]">
                      {bar.label}
                    </span>
                  </div>
                ))}
              </div>
              <div className="mt-4 grid grid-cols-3 gap-2 text-xs text-[#d9cdc0]">
                <span className="inline-flex items-center gap-1">
                  <CheckCircle size={14} className="text-[#c98146]" /> evidence
                </span>
                <span className="inline-flex items-center gap-1">
                  <Table size={14} className="text-[#c98146]" /> rows
                </span>
                <span className="inline-flex items-center gap-1">
                  <Warning size={14} className="text-[#c98146]" /> caveats
                </span>
              </div>
            </div>
          </div>
        </TiltSurface>
      </div>
    </div>
  );
}
