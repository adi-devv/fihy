import type { Category, GeoPoint, Issue, NewIssue, Severity, Status } from '../domain/issue';
import { CATEGORIES, SEVERITIES, categoryLabel } from '../domain/issue';
import type { AuthGateway, IssuesRepository, LocationService, NearbyQuery, Page, PhotoSource } from './repository';
import { PAGE_SIZE } from './repository';

export const demoLocation: GeoPoint = { latitude: 19.0607, longitude: 72.8362 };

/** Non-zero so the paging spinner is observable; tests set it to 0. */
export let pageLatency = 350;
export const setPageLatency = (ms: number) => {
  pageLatency = ms;
};

const LOCALITIES = [
  'Bandra East', 'Khar Road', 'Santacruz West', 'Dadar TT', 'Sion Circle',
  'Andheri East', 'Mahim Junction', 'Matunga', 'Vile Parle',
];

const base = (over: Partial<Issue> & Pick<Issue, 'id' | 'title' | 'description'>): Issue => ({
  category: 'other',
  severity: 'medium',
  status: 'reported',
  latitude: 19.06,
  longitude: 72.83,
  locality: null,
  confirmation_count: 0,
  confirmed_by_me: false,
  comment_count: 0,
  cover_url: null,
  created_at: new Date().toISOString(),
  ...over,
});

const daysAgo = (d: number) => new Date(Date.now() - d * 864e5).toISOString();

export const demoIssues: Issue[] = [
  base({
    id: 'demo-seed-1',
    title: 'Cover missing on the footpath side',
    description: 'Cover missing on the footpath side. Unlit after dark.',
    category: 'manhole',
    severity: 'high',
    status: 'community_verified',
    latitude: 19.0612, longitude: 72.8371,
    locality: 'Bandra East',
    confirmation_count: 7,
    created_at: daysAgo(6),
  }),
  base({
    id: 'demo-seed-2',
    title: 'Water collects across both lanes',
    description: 'Water collects across both lanes after any rain.',
    category: 'pothole_road',
    latitude: 19.0598, longitude: 72.8344,
    locality: 'Khar Road',
    confirmation_count: 2,
    created_at: daysAgo(3),
  }),
  base({
    id: 'demo-seed-3',
    title: 'Whole stretch dark between the market and the bridge',
    description: 'Whole stretch dark between the market and the bridge.',
    category: 'streetlight',
    severity: 'low',
    status: 'submitted_to_authority',
    latitude: 19.0623, longitude: 72.839,
    locality: 'Santacruz West',
    confirmation_count: 4,
    created_at: daysAgo(2),
  }),
  // Enough volume that the feed actually pages and the cursor gets exercised.
  ...Array.from({ length: 27 }, (_, i) => {
    const category = CATEGORIES[i % CATEGORIES.length] as Category;
    return base({
      id: `demo-seed-${i + 4}`,
      title: `${categoryLabel[category]} reported nearby`,
      description: `Residents flagged a ${categoryLabel[category].toLowerCase()} problem on this stretch. Reported ${i + 1} times this month.`,
      category,
      severity: SEVERITIES[i % SEVERITIES.length] as Severity,
      status: (['reported', 'community_verified', 'submitted_to_authority', 'in_progress'] as Status[])[i % 4],
      latitude: 19.05 + (i % 9) * 0.004,
      longitude: 72.83 + (i % 7) * 0.004,
      locality: LOCALITIES[i % LOCALITIES.length],
      confirmation_count: (i * 3) % 14,
      created_at: daysAgo(1 + i * 0.3),
    });
  }),
];

const sleep = (ms: number) => new Promise<void>((r) => setTimeout(r, ms));

export class FakeIssuesRepository implements IssuesRepository {
  private issues: Issue[];
  private nextId = 0;

  constructor(seed: Issue[] = demoIssues, private auth?: AuthGateway) {
    this.issues = [...seed];
  }

  async nearby({ category, cursor, limit = PAGE_SIZE }: NearbyQuery): Promise<Page> {
    await sleep(pageLatency);
    const matches = this.issues.filter((i) => !category || i.category === category);
    const offset = Number(cursor ?? 0) || 0;
    const items = matches.slice(offset, offset + limit);
    const consumed = offset + items.length;
    return { items, next_cursor: consumed >= matches.length ? null : String(consumed) };
  }

  async get(id: string) {
    const found = this.issues.find((i) => i.id === id);
    if (!found) throw new Error('That report is no longer available.');
    return found;
  }

  async confirm(id: string) {
    return this.setConfirmed(id, true);
  }

  async unconfirm(id: string) {
    return this.setConfirmed(id, false);
  }

  private setConfirmed(id: string, confirmed: boolean) {
    const index = this.issues.findIndex((i) => i.id === id);
    const current = this.issues[index];
    if (current.confirmed_by_me === confirmed) return current;
    const next: Issue = {
      ...current,
      confirmed_by_me: confirmed,
      confirmation_count: current.confirmation_count + (confirmed ? 1 : -1),
    };
    this.issues[index] = next;
    return next;
  }

  async create(draft: NewIssue): Promise<Issue> {
    const issue = base({
      id: `demo-${++this.nextId}`,
      title: draft.title,
      description: draft.description,
      category: draft.category,
      severity: draft.severity,
      latitude: draft.latitude,
      longitude: draft.longitude,
      locality: 'Your location',
      created_at: new Date().toISOString(),
    });
    this.issues.unshift(issue);
    return issue;
  }
}

/** Any phone signs in with [demoOtp]; no SMS provider involved. */
export class FakeAuthGateway implements AuthGateway {
  private userId: string | null;
  constructor(signedInAs: string | null = null, readonly demoOtp = '123456') {
    this.userId = signedInAs;
  }
  currentUserId() {
    return this.userId;
  }
  async requestOtp() {}
  async verifyOtp(_phone: string, code: string) {
    if (code !== this.demoOtp) {
      throw new Error(`Enter ${this.demoOtp} to sign in while in demo mode.`);
    }
    this.userId = 'demo-user';
  }
  async signOut() {
    this.userId = null;
  }
}

export class FixedLocationService implements LocationService {
  constructor(private point: GeoPoint = demoLocation) {}
  async current() {
    return this.point;
  }
}

/** Simulators have no camera, so demo runs hand back a placeholder path. */
export class StubPhotoSource implements PhotoSource {
  private count = 0;
  async capture() {
    return `demo://photo_${++this.count}.jpg`;
  }
}
