import type { ErrorEnvelope } from "@/lib/types";

export class ApiClientError extends Error {
  readonly code: string;
  readonly details: unknown | null;
  readonly requestId: string | null;
  readonly status: number;

  constructor(status: number, envelope: ErrorEnvelope) {
    super(envelope.error.message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = envelope.error.code;
    this.details = envelope.error.details;
    this.requestId = envelope.error.request_id;
  }
}

