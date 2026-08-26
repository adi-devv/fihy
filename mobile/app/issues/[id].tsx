import { useLocalSearchParams, useRouter } from 'expo-router';
import React from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useServices } from '../../src/data/context';
import { useConfirm, useIssue } from '../../src/data/queries';
import { categoryLabel, severityLabel, shortAge, statusLabel } from '../../src/domain/issue';
import { CategoryPlate } from '../../src/features/issues/CategoryPlate';
import { Centered, Notice } from '../../src/features/issues/NearbyFeed';
import { metric, type as t, useTone } from '../../src/theme/tokens';

/** The count is independent corroboration, so it reads as evidence
 *  accumulating rather than as a like. */
function CorroborationMeter({ count }: { count: number }) {
  const tone = useTone();
  const filled = Math.min(count, 10);
  return (
    <View style={styles.meter}>
      {Array.from({ length: 10 }, (_, i) => (
        <View
          key={i}
          style={{
            width: 5,
            height: i < filled ? 22 : 12,
            marginRight: 2.5,
            borderRadius: 1,
            backgroundColor: i < filled ? tone.accent : `${tone.ink}2e`,
          }}
        />
      ))}
      <Text style={[t.meta(15, '700', 0), { color: tone.ink, marginLeft: 8 }]}>
        {String(count).padStart(2, '0')}
      </Text>
      <Text style={[t.meta(10, '600', 1.2), { color: tone.chalk, marginLeft: 5 }]}>CONFIRMED</Text>
    </View>
  );
}

export default function IssueDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const tone = useTone();
  const router = useRouter();
  const { auth } = useServices();
  const confirm = useConfirm();
  const query = useIssue(id!);

  if (query.isPending) return <Centered><ActivityIndicator color={tone.accentDeep} /></Centered>;
  if (query.isError) return <Notice text={(query.error as Error).message} />;

  const issue = query.data;
  const critical = issue.severity === 'high';

  return (
    <ScrollView contentContainerStyle={{ padding: metric.gutter, paddingBottom: 48 }}>
      <View style={styles.row}>
        <Text style={[t.meta(10, '700'), { color: tone.ink }]}>
          {categoryLabel[issue.category].toUpperCase()}
        </Text>
        <View style={[styles.dot, { backgroundColor: critical ? tone.hazard : tone.chalk }]} />
        <Text style={[t.meta(9, '600'), { color: critical ? tone.hazard : tone.chalk }]}>
          {severityLabel[issue.severity].toUpperCase()}
        </Text>
        <View style={{ flex: 1 }} />
        <Text style={[t.meta(10, '500'), { color: tone.chalk }]}>{shortAge(issue.created_at)}</Text>
      </View>

      <Text style={[t.display(27, '700'), { color: tone.ink, marginTop: 12 }]}>{issue.title}</Text>
      <Text style={[t.body(16), { color: tone.chalk, marginTop: 10 }]}>{issue.description}</Text>

      <View style={{ marginTop: 18 }}>
        <CategoryPlate
          category={issue.category}
          severity={issue.severity}
          uri={issue.cover_url}
          height={230}
        />
      </View>

      <View style={[styles.divider, { backgroundColor: tone.hairline }]} />
      <CorroborationMeter count={issue.confirmation_count} />
      <Text style={[t.body(14), { color: tone.chalk, marginTop: 8 }]}>
        {issue.confirmation_count === 1
          ? 'One resident independently saw this.'
          : `${issue.confirmation_count} residents independently saw this.`}
      </Text>

      <Pressable
        onPress={() => {
          if (!auth.currentUserId()) return router.push('/auth');
          confirm.mutate({ id: issue.id, confirmed: issue.confirmed_by_me });
        }}
        style={[styles.cta, { backgroundColor: issue.confirmed_by_me ? tone.surface : tone.accent }]}>
        <Text style={[t.display(16, '600'), { color: issue.confirmed_by_me ? tone.ink : '#000' }]}>
          {issue.confirmed_by_me ? 'You confirmed this' : 'I independently saw this'}
        </Text>
      </Pressable>

      <Text style={[t.meta(10, '600', 1.4), { color: tone.chalk, marginTop: 14 }]}>
        STATUS  {statusLabel(issue.status).toUpperCase()}
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center' },
  dot: { width: 6, height: 6, borderRadius: 3, marginHorizontal: 8 },
  divider: { height: 1, marginVertical: 24 },
  meter: { flexDirection: 'row', alignItems: 'center' },
  cta: { height: 50, borderRadius: metric.radius, alignItems: 'center', justifyContent: 'center', marginTop: 20 },
});
