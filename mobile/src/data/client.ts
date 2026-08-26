import { ApiError } from './repository';

const BASE = process.env.EXPO_PUBLIC_API_URL ?? 'http://127.0.0.1:8000';

let token: string | null = null;
export const setToken = (next: string | null) => {
  token = next;
};
export const getToken = () => token;

/** The backend returns {detail} for errors; it is written for a person, so it
 *  is surfaced verbatim rather than replaced with a generic message. */
export async function request<T>(
  path: string,
  init: RequestInit & { query?: Record<string, unknown> } = {},
): Promise<T> {
  const { query, ...rest } = init;
  const url = new URL(path.replace(/^\//, ''), BASE.endsWith('/') ? BASE : `${BASE}/`);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null) url.searchParams.set(key, String(value));
  }
  const headers = new Headers(rest.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (rest.body && !(rest.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url.toString(), { ...rest, headers });
  if (response.status === 204) return undefined as T;
  const text = await response.text();
  const payload = text ? JSON.parse(text) : null;
  if (!response.ok) {
    throw new ApiError(payload?.detail ?? 'Something went wrong', response.status);
  }
  return payload as T;
}
