import React from 'react';
import {
  Ban, BadgeCheck, CheckCheck, CircleAlert, CircleCheck, CircleDot, Copy,
  Droplets, Flag, Footprints, HardHat, LampCeiling, Landmark, MailCheck,
  RotateCcw, Send, TrafficCone, Trash2, TreeDeciduous, TriangleAlert,
} from 'lucide-react-native';
import type { Category, Status } from '../../domain/issue';

const CATEGORY_ICON = {
  pothole_road: TriangleAlert,
  garbage: Trash2,
  footpath: Footprints,
  streetlight: LampCeiling,
  water_drainage: Droplets,
  manhole: CircleDot,
  traffic_infrastructure: TrafficCone,
  fallen_tree: TreeDeciduous,
  public_property: Landmark,
  other: CircleAlert,
} as const;

const STATUS_ICON = {
  reported: Flag,
  community_verified: BadgeCheck,
  submitted_to_authority: Send,
  authority_acknowledged: MailCheck,
  in_progress: HardHat,
  resolution_claimed: CircleCheck,
  resolved: CheckCheck,
  reopened: RotateCcw,
  duplicate: Copy,
  removed: Ban,
} as const;

export const CategoryGlyph = ({ category, ...rest }: { category: Category; size: number; color: string }) => {
  const Icon = CATEGORY_ICON[category];
  return <Icon {...rest} />;
};

export const StatusGlyph = ({ status, ...rest }: { status: Status; size: number; color: string }) => {
  const Icon = STATUS_ICON[status];
  return <Icon {...rest} />;
};
