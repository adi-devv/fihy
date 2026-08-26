import type { Issue, NewIssue } from '../domain/issue';
import { request } from './client';
import type { IssuesRepository, NearbyQuery, Page } from './repository';
import { PAGE_SIZE } from './repository';

export class ApiIssuesRepository implements IssuesRepository {
  nearby({ point, radiusM = 500, category, cursor, limit = PAGE_SIZE }: NearbyQuery) {
    return request<Page>('/issues/nearby', {
      query: {
        lat: point.latitude,
        lng: point.longitude,
        radius_m: radiusM,
        category,
        cursor,
        limit,
      },
    });
  }

  get(id: string) {
    return request<Issue>(`/issues/${id}`);
  }

  confirm(id: string) {
    return request<Issue>(`/issues/${id}/confirmations`, { method: 'POST' });
  }

  unconfirm(id: string) {
    return request<Issue>(`/issues/${id}/confirmations`, { method: 'DELETE' });
  }

  create(draft: NewIssue) {
    const form = new FormData();
    form.append('client_report_id', draft.client_report_id);
    form.append('title', draft.title);
    form.append('description', draft.description);
    form.append('category', draft.category);
    form.append('severity', draft.severity);
    form.append('latitude', String(draft.latitude));
    form.append('longitude', String(draft.longitude));
    draft.photos.forEach((uri, i) => {
      form.append('photos', {
        uri,
        name: `photo_${i}.jpg`,
        type: 'image/jpeg',
      } as unknown as Blob);
    });
    return request<Issue>('/issues', { method: 'POST', body: form });
  }
}
