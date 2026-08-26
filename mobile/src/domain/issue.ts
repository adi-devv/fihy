export const CATEGORIES = [
  'pothole_road', 'garbage', 'footpath', 'streetlight', 'water_drainage',
  'manhole', 'traffic_infrastructure', 'fallen_tree', 'public_property', 'other',
] as const;
export type Category = (typeof CATEGORIES)[number];

export const SEVERITIES = ['low', 'medium', 'high'] as const;
export type Severity = (typeof SEVERITIES)[number];

export const STATUSES = [
  'reported', 'community_verified', 'submitted_to_authority',
  'authority_acknowledged', 'in_progress', 'resolution_claimed', 'resolved',
  'reopened', 'duplicate', 'removed',
] as const;
export type Status = (typeof STATUSES)[number];

export type Issue = {
  id: string;
  title: string;
  description: string;
  category: Category;
  severity: Severity;
  status: Status;
  latitude: number;
  longitude: number;
  locality: string | null;
  confirmation_count: number;
  confirmed_by_me: boolean;
  comment_count: number;
  cover_url: string | null;
  created_at: string;
};

export type GeoPoint = { latitude: number; longitude: number };

export type NewIssue = {
  client_report_id: string;
  title: string;
  description: string;
  category: Category;
  severity: Severity;
  latitude: number;
  longitude: number;
  photos: string[];
};

export const categoryLabel: Record<Category, string> = {
  pothole_road: 'Pothole / Road',
  garbage: 'Garbage',
  footpath: 'Footpath',
  streetlight: 'Streetlight',
  water_drainage: 'Water / Drainage',
  manhole: 'Manhole',
  traffic_infrastructure: 'Traffic infrastructure',
  fallen_tree: 'Fallen tree',
  public_property: 'Public property',
  other: 'Other',
};

/** Only the top band is named, and only it earns the hazard red. */
export const severityLabel: Record<Severity, string> = {
  high: 'Critical',
  medium: 'Medium',
  low: 'Low',
};

export const statusLabel = (status: Status) =>
  status.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

export const shortAge = (iso: string) => {
  const ms = Date.now() - new Date(iso).getTime();
  const m = Math.floor(ms / 60000);
  if (m < 1) return 'now';
  if (m < 60) return `${m}m`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h`;
  return `${Math.floor(h / 24)}d`;
};
