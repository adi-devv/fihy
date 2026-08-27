import { Camera, BadgeCheck } from 'lucide-react-native';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import type { Issue } from '../../domain/issue';
import { metric, type as t, useTone } from '../../theme/tokens';

type Shape = Pick<Issue, 'photo_support_count' | 'photo_supports_needed' | 'confirmed_at'>;

const prompt = (needed: number) =>
  needed === 1
    ? 'One more photo confirms this'
    : `${needed} more photos confirm this`;

/**
 * What actually confirms a report: another person standing in the same place
 * with a camera. The counts elsewhere treat a tap and a photograph alike, so
 * without this the distinction the model is built on is invisible, and nobody
 * is told the one thing that would move the report along.
 */
export function ConfirmationBar({ issue, compact = false }: { issue: Shape; compact?: boolean }) {
  const tone = useTone();
  const total = issue.photo_support_count + issue.photo_supports_needed;
  const confirmed = issue.confirmed_at !== null;

  if (confirmed && compact) return null;

  return (
    <View style={compact ? styles.compact : [styles.block, { borderColor: tone.hairline }]}>
      <View style={styles.row}>
        {confirmed ? (
          <BadgeCheck size={compact ? 14 : 17} color={tone.accentDeep} />
        ) : (
          <Camera size={compact ? 14 : 17} color={tone.ink} />
        )}
        <Text
          style={[
            t.meta(compact ? 11 : 12, '700', 0.2),
            { color: confirmed ? tone.accentDeep : tone.ink, marginLeft: 7 },
          ]}>
          {confirmed ? 'Confirmed by photo' : prompt(issue.photo_supports_needed)}
        </Text>
        {!compact && (
          <>
            <View style={{ flex: 1 }} />
            <Text
              style={[
                t.meta(12, '700', 0),
                { color: confirmed ? tone.accentDeep : tone.ink },
              ]}>
              {issue.photo_support_count}/{total}
            </Text>
          </>
        )}
      </View>

      {!compact && (
        <>
          <View style={styles.pips}>
            {Array.from({ length: total }, (_, i) => (
              <View
                key={i}
                style={[
                  styles.pip,
                  {
                    backgroundColor:
                      i < issue.photo_support_count ? tone.accent : `${tone.ink}22`,
                  },
                ]}
              />
            ))}
          </View>
          <Text style={[t.body(13), { color: tone.chalk, marginTop: 9 }]}>
            {confirmed
              ? 'Enough people photographed this that it counts as corroborated, and it can be raised with the authority.'
              : 'A photograph from someone else is what confirms a report. Tapping support helps, but only a photo counts here.'}
          </Text>
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  block: {
    borderWidth: 1,
    borderRadius: metric.radius,
    padding: 13,
    marginTop: 18,
    marginBottom: 20,
  },
  compact: { marginTop: 8 },
  row: { flexDirection: 'row', alignItems: 'center' },
  pips: { flexDirection: 'row', marginTop: 11 },
  pip: { flex: 1, height: 5, borderRadius: 3, marginRight: 4 },
});
