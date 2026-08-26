import type { Category, GeoPoint, Issue, NewIssue } from '../domain/issue';

export const PAGE_SIZE = 20;

/** Opaque to the client: it round-trips whatever the backend hands back. */
export type Page = { items: Issue[]; next_cursor: string | null };

export type NearbyQuery = {
  point: GeoPoint;
  radiusM?: number;
  category?: Category;
  cursor?: string | null;
  limit?: number;
};

export interface IssuesRepository {
  nearby(query: NearbyQuery): Promise<Page>;
  get(id: string): Promise<Issue>;
  confirm(id: string): Promise<Issue>;
  unconfirm(id: string): Promise<Issue>;
  create(draft: NewIssue): Promise<Issue>;
}

export interface AuthGateway {
  currentUserId(): string | null;
  requestOtp(phone: string): Promise<void>;
  verifyOtp(phone: string, code: string): Promise<void>;
  signOut(): Promise<void>;
}

export interface LocationService {
  current(): Promise<GeoPoint>;
}

export interface PhotoSource {
  capture(): Promise<string | null>;
}

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}
