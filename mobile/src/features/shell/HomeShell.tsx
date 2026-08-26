import { useRouter } from 'expo-router';
import { Plus, User } from 'lucide-react-native';
import React, { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Svg, { Defs, LinearGradient, Stop, Circle } from 'react-native-svg';
import { useServices } from '../../data/context';
import { useLocation } from '../../data/queries';
import { Centered, Notice, NearbyFeed } from '../issues/NearbyFeed';
import { MapScreen } from '../issues/MapScreen';
import { metric, type as t, useTone } from '../../theme/tokens';
import { NavIcon, type NavIconName } from './NavIcon';

const SECTIONS: NavIconName[] = ['house', 'search', 'bell'];

export function HomeShell() {
  const tone = useTone();
  const router = useRouter();
  const { auth } = useServices();
  const [tab, setTab] = useState(0);
  const [section, setSection] = useState(0);
  const [chromeVisible, setChromeVisible] = useState(true);
  const location = useLocation();

  return (
    <View style={{ flex: 1, backgroundColor: tone.bg }}>
      <SafeAreaView edges={['top']} style={{ backgroundColor: tone.bg }}>
        {chromeVisible && (
          <View style={styles.masthead}>
            <View style={{ width: 34 }} />
            <Mark />
            <Pressable
              onPress={() => router.push('/auth')}
              style={[
                styles.avatar,
                {
                  backgroundColor: tone.surface,
                  borderColor: auth.currentUserId() ? tone.accent : tone.hairline,
                  borderWidth: auth.currentUserId() ? 1.8 : 1,
                },
              ]}>
              <User size={19} color={tone.chalk} />
            </Pressable>
          </View>
        )}
        <View style={[styles.tabs, { borderBottomColor: tone.hairline }]}>
          {['Nearby', 'Map'].map((label, i) => (
            <Pressable key={label} style={styles.tab} onPress={() => setTab(i)}>
              <Text style={[t.display(15, '700'), { color: i === tab ? tone.ink : tone.chalk }]}>
                {label}
              </Text>
              <View
                style={[
                  styles.indicator,
                  { backgroundColor: i === tab ? tone.accent : 'transparent' },
                ]}
              />
            </Pressable>
          ))}
        </View>
      </SafeAreaView>

      <View style={{ flex: 1 }}>
        {location.isPending && <Centered><ActivityIndicator color={tone.accentDeep} /></Centered>}
        {location.isError && <Notice text={(location.error as Error).message} />}
        {location.data &&
          (tab === 0 ? (
            <NearbyFeed point={location.data} onScrollDirection={setChromeVisible} />
          ) : (
            <MapScreen point={location.data} />
          ))}
      </View>

      <Pressable
        onPress={() => router.push('/report')}
        style={[styles.fab, { backgroundColor: tone.accent }]}>
        <Plus size={30} color="#000" />
      </Pressable>

      {chromeVisible && (
        <SafeAreaView edges={['bottom']} style={{ backgroundColor: tone.bg }}>
          <View style={[styles.sectionBar, { borderTopColor: tone.hairline }]}>
            {SECTIONS.map((name, i) => (
              <Pressable key={name} style={styles.section} onPress={() => setSection(i)}>
                <NavIcon
                  name={name}
                  filled={i === section}
                  color={i === section ? tone.accentDeep : tone.chalk}
                />
              </Pressable>
            ))}
          </View>
        </SafeAreaView>
      )}
    </View>
  );
}

/** The app mark: a single gradient dot, no wordmark. */
function Mark() {
  const tone = useTone();
  return (
    <Svg width={26} height={26} viewBox="0 0 26 26">
      <Defs>
        <LinearGradient id="mark" x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0" stopColor={tone.accentSoft} />
          <Stop offset="1" stopColor={tone.accentDeep} />
        </LinearGradient>
      </Defs>
      <Circle cx={13} cy={13} r={13} fill="url(#mark)" />
    </Svg>
  );
}

const styles = StyleSheet.create({
  masthead: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: metric.gutter, paddingTop: 6, paddingBottom: 8,
  },
  avatar: { width: 34, height: 34, borderRadius: 17, alignItems: 'center', justifyContent: 'center' },
  tabs: { flexDirection: 'row', borderBottomWidth: 1 },
  tab: { flex: 1, alignItems: 'center' },
  indicator: { height: 3, width: 34, borderRadius: 2, marginTop: 8 },
  fab: {
    position: 'absolute', right: 20, bottom: 90, width: 58, height: 58,
    borderRadius: 29, alignItems: 'center', justifyContent: 'center',
  },
  sectionBar: { flexDirection: 'row', height: 52, borderTopWidth: 1 },
  section: { flex: 1, alignItems: 'center', justifyContent: 'center' },
});
