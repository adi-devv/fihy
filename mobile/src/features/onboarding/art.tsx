import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import Svg, { Circle, Defs, LinearGradient, Path, Rect, Stop } from 'react-native-svg';
import type { Category } from '../../domain/issue';
import { type as t, useTone } from '../../theme/tokens';
import { CategoryGlyph, StatusGlyph } from '../issues/glyphs';

const SHOWN: Category[] = [
  'pothole_road', 'manhole', 'streetlight', 'garbage',
  'water_drainage', 'footpath', 'fallen_tree', 'traffic_infrastructure',
];

/** What can be reported, as the glyphs the rest of the app uses. */
export function ReportArt() {
  const tone = useTone();
  return (
    <View style={styles.grid}>
      {SHOWN.map((category, i) => (
        <View
          key={category}
          style={[
            styles.tile,
            {
              borderColor: tone.hairline,
              backgroundColor: i === 1 ? `${tone.accent}1f` : 'transparent',
            },
          ]}>
          <CategoryGlyph
            category={category}
            size={26}
            color={i === 1 ? tone.accentDeep : tone.chalk}
          />
        </View>
      ))}
    </View>
  );
}

/** The confirmation bar, filling. The one mechanic worth teaching up front. */
export function ConfirmArt() {
  const tone = useTone();
  return (
    <View style={styles.confirm}>
      {[0, 1, 2].map((step) => (
        <View key={step} style={styles.confirmRow}>
          <View style={styles.pips}>
            {[0, 1].map((pip) => (
              <View
                key={pip}
                style={[
                  styles.pip,
                  { backgroundColor: pip < step ? tone.accent : `${tone.ink}1a` },
                ]}
              />
            ))}
          </View>
          <Text
            style={[
              t.meta(11, '700', 0.3),
              { color: step === 2 ? tone.accentDeep : tone.chalk, marginLeft: 12 },
            ]}>
            {step === 2 ? 'Confirmed' : `${step} of 2 photos`}
          </Text>
        </View>
      ))}
    </View>
  );
}

/** Where a confirmed report goes. A compressed StatusTrack. */
export function EscalateArt() {
  const tone = useTone();
  const steps: { status: Parameters<typeof StatusGlyph>[0]['status']; label: string }[] = [
    { status: 'community_verified', label: 'Confirmed' },
    { status: 'submitted_to_authority', label: 'Sent to the ward' },
    { status: 'resolved', label: 'Fixed' },
  ];
  return (
    <View style={styles.track}>
      {steps.map((step, i) => (
        <View key={step.label} style={styles.trackRow}>
          <View style={styles.trackMark}>
            <View style={[styles.node, { borderColor: tone.accent, backgroundColor: tone.accent }]}>
              <StatusGlyph status={step.status} size={14} color="#000" />
            </View>
            {i < steps.length - 1 && (
              <View style={[styles.stem, { backgroundColor: tone.hairline }]} />
            )}
          </View>
          <Text style={[t.display(15, '600'), { color: tone.ink, marginLeft: 12, marginTop: 4 }]}>
            {step.label}
          </Text>
        </View>
      ))}
    </View>
  );
}

/** A pin over a soft radius: what "near me" means. */
export function LocationArt() {
  const tone = useTone();
  return (
    <Svg width={168} height={168} viewBox="0 0 168 168">
      <Defs>
        <LinearGradient id="halo" x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0" stopColor={tone.accentSoft} stopOpacity={0.55} />
          <Stop offset="1" stopColor={tone.accentDeep} stopOpacity={0.16} />
        </LinearGradient>
      </Defs>
      <Circle cx={84} cy={84} r={72} fill="url(#halo)" />
      <Circle cx={84} cy={84} r={46} fill="none" stroke={tone.accentDeep} strokeOpacity={0.35} strokeWidth={1.5} />
      <Circle cx={84} cy={84} r={22} fill="none" stroke={tone.accentDeep} strokeOpacity={0.5} strokeWidth={1.5} />
      <Path
        d="M84 62a15 15 0 0 0-15 15c0 11 15 27 15 27s15-16 15-27a15 15 0 0 0-15-15z"
        fill={tone.ink}
      />
      <Circle cx={84} cy={77} r={5.5} fill={tone.bg} />
      <Rect x={0} y={0} width={0} height={0} fill="none" />
    </Svg>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row', flexWrap: 'wrap', width: 232,
    alignItems: 'center', justifyContent: 'center',
  },
  tile: {
    width: 48, height: 48, borderRadius: 12, borderWidth: 1, margin: 4,
    alignItems: 'center', justifyContent: 'center',
  },
  confirm: { width: 214 },
  confirmRow: { flexDirection: 'row', alignItems: 'center', marginVertical: 9 },
  pips: { flexDirection: 'row', width: 96 },
  pip: { flex: 1, height: 7, borderRadius: 4, marginRight: 5 },
  track: { width: 214 },
  trackRow: { flexDirection: 'row' },
  trackMark: { alignItems: 'center' },
  node: {
    width: 26, height: 26, borderRadius: 13, borderWidth: 1.5,
    alignItems: 'center', justifyContent: 'center',
  },
  stem: { width: 2, height: 26 },
});
