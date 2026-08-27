import React from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';
import Svg, { Defs, LinearGradient, Rect, Stop } from 'react-native-svg';
import { initials } from '../../domain/profile';
import { type as t } from '../../theme/tokens';

/**
 * Fixed rather than theme-derived: the gradient is the same in both themes, so
 * letting the ink follow the theme would give one person two different faces.
 * Dark ink also holds up across the whole ramp, where white washes out at the
 * light end.
 */
const INITIAL_INK = '#101014';

/** Deterministic hue from the id, so a person keeps the same face everywhere. */
const hue = (seed: string) => {
  let total = 0;
  for (let i = 0; i < seed.length; i += 1) total = (total * 31 + seed.charCodeAt(i)) % 360;
  return total;
};

export function Avatar({
  id,
  name,
  uri,
  size = 64,
}: {
  id: string;
  name: string;
  uri?: string | null;
  size?: number;
}) {
  const radius = size / 2;

  if (uri) {
    return (
      <Image
        source={{ uri }}
        style={{ width: size, height: size, borderRadius: radius }}
        resizeMode="cover"
      />
    );
  }

  const base = hue(id);
  const gradient = `avatar-${id}`;
  return (
    <View style={{ width: size, height: size, borderRadius: radius, overflow: 'hidden' }}>
      <Svg width={size} height={size} style={StyleSheet.absoluteFill}>
        <Defs>
          <LinearGradient id={gradient} x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0" stopColor={`hsl(${base}, 72%, 68%)`} />
            <Stop offset="1" stopColor={`hsl(${(base + 48) % 360}, 68%, 44%)`} />
          </LinearGradient>
        </Defs>
        <Rect width={size} height={size} fill={`url(#${gradient})`} />
      </Svg>
      <View style={styles.center}>
        <Text style={[t.display(size * 0.36, '700'), { color: INITIAL_INK }]}>
          {initials(name)}
        </Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
});
