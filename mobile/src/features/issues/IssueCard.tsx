import { ArrowUp, Eye, MapPin } from 'lucide-react-native';
import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { Issue } from '../../domain/issue';
import { categoryLabel, severityLabel, shortAge } from '../../domain/issue';
import { metric, type as t, useTone } from '../../theme/tokens';
import { CategoryPlate } from './CategoryPlate';
import { ConfirmationBar } from './ConfirmationBar';
import { StatusIcon } from './StatusChip';

export function IssueCard({
  issue,
  onPress,
  onConfirm,
}: {
  issue: Issue;
  onPress: () => void;
  onConfirm: () => void;
}) {
  const tone = useTone();
  const critical = issue.severity === 'high';
  const text = issue.description.trim() || issue.title;

  return (
    <Pressable onPress={onPress} style={[styles.card, { borderBottomColor: tone.hairline }]}>
      <View style={styles.metaRow}>
        <MapPin size={14} color={tone.ink} />
        <View style={styles.metaLeft}>
          <Text numberOfLines={1} style={[t.meta(12, '600', 0), { color: tone.ink, flexShrink: 1 }]}>
            {issue.locality ?? categoryLabel[issue.category]}
          </Text>
          <Text style={[t.meta(12, '400', 0), { color: tone.chalk }]}>{'  ·  '}</Text>
          <Text
            style={[
              t.meta(12, critical ? '700' : '500', 0),
              { color: critical ? tone.hazard : tone.chalk },
            ]}>
            {severityLabel[issue.severity]}
          </Text>
        </View>
        <Text style={[t.meta(12, '500', 0), { color: tone.chalk }]}>{shortAge(issue.created_at)}</Text>
      </View>

      <Text numberOfLines={4} style={[t.display(16.5, '500'), { color: tone.ink, marginTop: 9 }]}>
        {text}
      </Text>

      <View style={{ marginTop: 12 }}>
        <CategoryPlate category={issue.category} severity={issue.severity} uri={issue.cover_url} />
      </View>

      <View style={styles.actions}>
        <Pill
          icon={ArrowUp}
          label={String(issue.comment_count)}
          emphasised
          onPress={onPress}
        />
        <Pill
          icon={Eye}
          label={String(issue.confirmation_count)}
          active={issue.confirmed_by_me}
          onPress={onConfirm}
        />
        <View style={{ flex: 1 }} />
        <StatusIcon status={issue.status} size={19} />
      </View>

      <ConfirmationBar issue={issue} compact />
    </Pressable>
  );
}

function Pill({
  icon: Icon,
  label,
  onPress,
  emphasised = false,
  active = false,
}: {
  icon: React.ComponentType<{ size: number; color: string }>;
  label: string;
  onPress: () => void;
  emphasised?: boolean;
  active?: boolean;
}) {
  const tone = useTone();
  const ink = emphasised || active ? tone.accentDeep : tone.chalk;
  return (
    <Pressable
      onPress={onPress}
      hitSlop={6}
      style={[
        styles.pill,
        emphasised
          ? { backgroundColor: `${tone.accent}24` }
          : { borderWidth: 1, borderColor: active ? tone.accent : tone.hairline },
      ]}>
      <Icon size={17} color={ink} />
      <Text style={[t.meta(13, '700', 0), { color: ink, marginLeft: 6 }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { paddingHorizontal: metric.gutter, paddingTop: 14, paddingBottom: 8, borderBottomWidth: 1 },
  metaRow: { flexDirection: 'row', alignItems: 'center' },
  metaLeft: { flexDirection: 'row', alignItems: 'center', flex: 1, marginLeft: 4 },
  actions: { flexDirection: 'row', alignItems: 'center', marginTop: 6, minHeight: 44 },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 11,
    paddingVertical: 7,
    borderRadius: 999,
    marginRight: 8,
  },
});
