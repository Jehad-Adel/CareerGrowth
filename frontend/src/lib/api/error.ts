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
}
