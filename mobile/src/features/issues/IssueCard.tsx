import { ArrowUp, MapPin, MessageSquare } from 'lucide-react-native';
import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { Issue } from '../../domain/issue';
import { categoryLabel, severityLabel, shortAge, statusLabel } from '../../domain/issue';
import { metric, type as t, useTone } from '../../theme/tokens';
import { CategoryPlate } from './CategoryPlate';
import { StatusGlyph } from './glyphs';

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
        <MapPin size={14} color={tone.chalk} />
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
          label={String(issue.confirmation_count)}
          emphasised
          active={issue.confirmed_by_me}
          onPress={onConfirm}
        />
        <Pill icon={MessageSquare} label={String(issue.comment_count)} onPress={onPress} />
        <View style={{ flex: 1 }} />
        <StatusGlyph status={issue.status} size={19} color={tone.chalk} />
      </View>
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
  const tint = emphasised ? tone.accentDeep : tone.chalk;
  return (
    <Pressable
      onPress={onPress}
      hitSlop={6}
      style={[
        styles.pill,
        emphasised
          ? { backgroundColor: active ? tone.accent : `${tone.accent}24` }
          : { borderWidth: 1, borderColor: tone.hairline },
      ]}>
      <Icon size={17} color={active ? '#000' : tint} />
      <Text style={[t.meta(13, '700', 0), { color: active ? '#000' : tint, marginLeft: 6 }]}>
        {label}
      </Text>
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
