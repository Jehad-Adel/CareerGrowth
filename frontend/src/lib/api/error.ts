/**
 * The one error type every API path throws.
 *
 * Lives in its own module so server-only code can catch it without dragging a
 * browser Supabase client into the server bundle.
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }

  get isRateLimit(): boolean {
    return this.status === 429;
  }

  get isAuthError(): boolean {
    return this.status === 401 || this.status === 403;
  }

  get isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }

  get isServerError(): boolean {
    return this.status >= 500;
  }
}

/**
 * Normalizes any caught error (network offline/DNS, API 4xx/429/5xx, timeouts)
 * into a safe, user-friendly message without leaking stack traces or internals.
 */
export function normalizeApiError(
  error: unknown,
  fallbackMessage = "Something went wrong. Please try again shortly.",
): string {
  if (error instanceof ApiError) {
    if (error.isRateLimit) {
      return (
        error.message ||
        "You're doing that a bit too quickly. Please wait a moment and try again."
      );
    }
    if (error.isServerError) {
      return "Our servers encountered a temporary issue. Please try again shortly.";
    }
    return error.message;
  }

  if (error instanceof Error) {
    if (error.name === "AbortError" || error.name === "TimeoutError") {
      return "The request took too long to complete. Please check your connection and try again.";
    }
    if (
      error.message.toLowerCase().includes("fetch failed") ||
      error.message.toLowerCase().includes("networkerror")
    ) {
      return "Unable to connect to the server. Please check your internet connection.";
    }
  }

  return fallbackMessage;
}

