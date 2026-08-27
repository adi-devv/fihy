import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import type { Status } from '../../domain/issue';
import { statusLabel } from '../../domain/issue';
import type { StatusTone } from '../../domain/status';
import { STATUS_META } from '../../domain/status';
import { type Tones, type as t, useTone } from '../../theme/tokens';
import { StatusGlyph } from './glyphs';

const ink = (tone: Tones, of: StatusTone): string => {
  switch (of) {
    case 'good':
      return tone.accentDeep;
    case 'warn':
      return tone.hazard;
    case 'progress':
      return tone.ink;
    default:
      return tone.chalk;
  }
};

/**
 * Status where there is no room for words: a feed card, a row in the duplicate
 * sheet. The tone carries the meaning, and the label goes to screen readers
 * rather than being dropped.
 */
export function StatusIcon({ status, size = 19 }: { status: Status; size?: number }) {
  const tone = useTone();
  return (
    <View accessibilityLabel={statusLabel(status)}>
      <StatusGlyph
        status={status}
        size={size}
        color={ink(tone, STATUS_META[status].tone)}
      />
    </View>
  );
}

/**
 * Status spelled out, for the report page, where it is the answer to "what is
 * happening with this?" rather than a glance.
 */
export function StatusChip({ status, size = 14 }: { status: Status; size?: number }) {
  const tone = useTone();
  const colour = ink(tone, STATUS_META[status].tone);
  return (
    <View style={[styles.row, styles.pill, { backgroundColor: tone.surface }]}>
      <StatusGlyph status={status} size={size + 2} color={colour} />
      <Text style={[t.meta(size, '600', 0), { color: colour, marginLeft: 6 }]}>
        {statusLabel(status)}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center' },
  pill: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    alignSelf: 'flex-start',
  },
});
