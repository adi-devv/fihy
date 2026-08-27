import { ChevronDown, ChevronUp, Landmark } from 'lucide-react-native';
import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import type { Escalation } from '../../domain/escalation';
import { escalationLabel } from '../../domain/escalation';
import { metric, type as t, useTone } from '../../theme/tokens';

const sentLabel = (iso: string | null) => {
  if (!iso) return null;
  const date = new Date(iso);
  return Number.isNaN(date.getTime())
    ? null
    : date.toLocaleDateString(undefined, { day: 'numeric', month: 'long', year: 'numeric' });
};

/**
 * The letter that went out on the residents' behalf, readable by them.
 * Collapsed by default: the fact that it was sent, and to whom, is what most
 * people want; the wording matters to the few who ask for it.
 */
export function EscalationCard({ escalation }: { escalation: Escalation }) {
  const tone = useTone();
  const [open, setOpen] = useState(false);
  const sent = sentLabel(escalation.sent_at);
  const trouble = escalation.state === 'failed' || escalation.state === 'bounced';

  return (
    <View style={[styles.card, { borderColor: tone.hairline }]}>
      <View style={styles.head}>
        <Landmark size={17} color={tone.chalk} />
        <Text style={[t.meta(11, '600', 0), { color: tone.chalk, marginLeft: 7 }]}>
          Raised with
        </Text>
      </View>

      <Text style={[t.display(17, '600'), { color: tone.ink, marginTop: 7 }]}>
        {escalation.authority}
      </Text>

      <View style={styles.meta}>
        <Text
          style={[
            t.meta(11, '700', 0.3),
            { color: trouble ? tone.hazard : tone.accentDeep },
          ]}>
          {escalationLabel[escalation.state]}
        </Text>
        {sent && (
          <Text style={[t.meta(11, '500', 0.3), { color: tone.chalk, marginLeft: 8 }]}>
            {sent}
          </Text>
        )}
      </View>

      {escalation.reference && (
        <Text style={[t.body(13), { color: tone.chalk, marginTop: 6 }]}>
          Reference {escalation.reference}
        </Text>
      )}
      {escalation.detail && (
        <Text
          style={[
            t.body(13),
            { color: trouble ? tone.hazard : tone.chalk, marginTop: 6 },
          ]}>
          {escalation.detail}
        </Text>
      )}

      <Pressable onPress={() => setOpen(!open)} style={styles.toggle} hitSlop={6}>
        <Text style={[t.meta(11, '700', 0.3), { color: tone.accentDeep }]}>
          {open ? 'Hide the letter' : 'Read the letter'}
        </Text>
        {open ? (
          <ChevronUp size={15} color={tone.accentDeep} />
        ) : (
          <ChevronDown size={15} color={tone.accentDeep} />
        )}
      </Pressable>

      {open && (
        <View style={[styles.letter, { borderTopColor: tone.hairline }]}>
          <Text style={[t.meta(11, '700', 0.3), { color: tone.chalk }]}>
            {escalation.subject}
          </Text>
          <Text style={[t.body(14), { color: tone.ink, marginTop: 9 }]}>
            {escalation.body}
          </Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { borderWidth: 1, borderRadius: metric.radius, padding: 14, marginTop: 18 },
  head: { flexDirection: 'row', alignItems: 'center' },
  meta: { flexDirection: 'row', alignItems: 'center', marginTop: 7 },
  toggle: { flexDirection: 'row', alignItems: 'center', gap: 5, marginTop: 12 },
  letter: { borderTopWidth: 1, marginTop: 12, paddingTop: 12 },
});
