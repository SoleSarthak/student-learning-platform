import { clearToken, getToken } from "@/lib/auth";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export function errorMessage(err: unknown, fallback = "Something went wrong") {
  return err instanceof Error ? err.message : fallback;
}

function extractMessage(data: unknown): string {
  if (data && typeof data === "object") {
    const body = data as {
      error?: { message?: unknown; details?: unknown };
      detail?: unknown;
    };

    // Validation errors: show the first problem, e.g.
    // "password: String should have at least 8 characters".
    const details = body.error?.details;

    if (Array.isArray(details) && details.length > 0) {
      const first = details[0] as { msg?: unknown; loc?: unknown };

      if (typeof first?.msg === "string") {
        const field = Array.isArray(first.loc)
          ? String(first.loc[first.loc.length - 1])
          : "";

        return field ? `${field}: ${first.msg}` : first.msg;
      }
    }

    if (typeof body.error?.message === "string") return body.error.message;
    if (typeof body.detail === "string") return body.detail;
  }

  return "Something went wrong";
}

export async function apiRequest<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;

  try {
    response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
      cache: "no-store",
    });
  } catch {
    throw new ApiError(
      "Cannot reach the server. Check your connection and try again.",
      0
    );
  }

  const data: unknown =
    response.status === 204 ? null : await response.json().catch(() => null);

  if (!response.ok) {
    // Our session expired or the token is invalid: log the user out so the
    // UI (navbar, protected pages) reacts immediately.
    if (response.status === 401 && token) {
      clearToken();
    }

    throw new ApiError(extractMessage(data), response.status);
  }

  return data as T;
}
