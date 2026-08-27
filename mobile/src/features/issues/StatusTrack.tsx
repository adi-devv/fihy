import { Check } from 'lucide-react-native';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import type { Issue, Stage, StageState } from '../../domain/issue';
import { stagesFor } from '../../domain/issue';
import { type as t, useTone } from '../../theme/tokens';

const RAIL = 22;
const NODE = 15;

/**
 * Where a report has got to.
 *
 * Vertical rather than the usual horizontal tracker: the path forks, and one of
 * the labels names a municipal body, neither of which survives being squeezed
 * into a phone's width. Reading down also matches how the rest of the page
 * moves.
 */
export function StatusTrack({
  issue,
  authority = null,
}: {
  issue: Issue;
  authority?: string | null;
}) {
  const tone = useTone();
  const { trunk, fork } = stagesFor(issue, authority);

  return (
    <View>
      {trunk.map((stage, index) => (
        <Row key={stage.key} stage={stage} rail={index < trunk.length - 1} />
      ))}

      <View style={styles.stemRow}>
        <View style={styles.gutter}>
          <View style={[styles.stem, { backgroundColor: tone.hairline }]} />
        </View>
        <Text style={[t.body(13), { color: tone.chalk, marginLeft: 12 }]}>then one of</Text>
      </View>

      <View style={styles.branches}>
        <View style={styles.branch}>
          <Branch stage={fork[0]} />
        </View>
        <Text style={[t.body(13), { color: tone.chalk, width: 26, textAlign: 'center' }]}>or</Text>
        <View style={styles.branch}>
          <Branch stage={fork[1]} />
        </View>
      </View>
    </View>
  );
}

function paint(state: StageState, tone: ReturnType<typeof useTone>) {
  if (state === 'done') return { fill: tone.accent, ring: tone.accent, ink: tone.ink };
  if (state === 'current') return { fill: 'transparent', ring: tone.accent, ink: tone.ink };
  return { fill: 'transparent', ring: tone.hairline, ink: tone.chalk };
}

function Node({ state }: { state: StageState }) {
  const tone = useTone();
  const { fill, ring } = paint(state, tone);
  return (
    <View
      style={[
        styles.node,
        { backgroundColor: fill, borderColor: ring, borderWidth: state === 'done' ? 0 : 2 },
      ]}>
      {state === 'done' && <Check size={10} color="#000" strokeWidth={3.5} />}
    </View>
  );
}

function Row({ stage, rail }: { stage: Stage; rail: boolean }) {
  const tone = useTone();
  const { ink } = paint(stage.state, tone);
  return (
    <View style={styles.row}>
      <View style={styles.gutter}>
        <Node state={stage.state} />
        {rail && <View style={[styles.rail, { backgroundColor: tone.hairline }]} />}
      </View>
      <View style={[styles.label, rail && { paddingBottom: 16 }]}>
        <Text style={[t.display(15, stage.state === 'pending' ? '500' : '600'), { color: ink }]}>
          {stage.label}
        </Text>
        {stage.caption && (
          <Text style={[t.body(13), { color: tone.chalk, marginTop: 2 }]}>{stage.caption}</Text>
        )}
      </View>
    </View>
  );
}

function Branch({ stage }: { stage: Stage }) {
  const tone = useTone();
  const { ink } = paint(stage.state, tone);
  const lit = stage.state !== 'pending';
  return (
    <View
      style={[
        styles.branchBox,
        {
          borderColor: lit ? tone.accent : tone.hairline,
          backgroundColor: lit ? `${tone.accent}14` : 'transparent',
        },
      ]}>
      <Node state={stage.state} />
      <Text
        style={[
          t.display(14, lit ? '600' : '500'),
          { color: ink, marginTop: 8 },
        ]}>
        {stage.label}
      </Text>
      {stage.caption && (
        <Text style={[t.body(12), { color: tone.chalk, marginTop: 3 }]}>{stage.caption}</Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row' },
  gutter: { width: RAIL, alignItems: 'center' },
  node: {
    width: NODE,
    height: NODE,
    borderRadius: NODE / 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rail: { width: 2, flex: 1, marginVertical: 3 },
  label: { flex: 1, marginLeft: 12, marginTop: -2 },
  stemRow: { flexDirection: 'row', alignItems: 'center', height: 26 },
  stem: { width: 2, height: 26 },
  branches: { flexDirection: 'row', alignItems: 'center', marginTop: 8 },
  branch: { flex: 1 },
  branchBox: { borderWidth: 1, borderRadius: 10, padding: 12, minHeight: 96 },
});
