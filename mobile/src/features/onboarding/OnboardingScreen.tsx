import { useRouter } from 'expo-router';
import React, { useCallback, useRef, useState } from 'react';
import {
  Dimensions,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useServices } from '../../data/context';
import { markOnboardingSeen } from '../../data/startup';
import { metric, type as t, useTone } from '../../theme/tokens';
import { ConfirmArt, EscalateArt, LocationArt, ReportArt } from './art';

type Slide = {
  key: string;
  art: () => React.ReactElement;
  title: string;
  body: string;
};

const SLIDES: Slide[] = [
  {
    key: 'report',
    art: ReportArt,
    title: 'Report what is broken',
    body: 'A missing manhole cover, a dark street, a drain that floods every monsoon. Photograph it, and it is on the map for your neighbours.',
  },
  {
    key: 'confirm',
    art: ConfirmArt,
    title: 'Neighbours confirm it',
    body: 'Anyone can back a report. But it takes photographs from two other people, standing in the same place, before it counts as corroborated. That is what makes it hard to ignore.',
  },
  {
    key: 'escalate',
    art: EscalateArt,
    title: 'Then it goes to the ward',
    body: 'Confirmed reports are raised with the authority responsible for them, and you can read the letter that went out on your behalf.',
  },
  {
    key: 'location',
    art: LocationArt,
    title: 'Start with what is near you',
    body: 'Your location places a report accurately and shows what has already been flagged nearby. It is only sent with a report you choose to file.',
  },
];

export function OnboardingScreen() {
  const tone = useTone();
  const router = useRouter();
  const { location } = useServices();
  const scroller = useRef<ScrollView>(null);
  const [index, setIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const width = Dimensions.get('window').width;

  const last = index === SLIDES.length - 1;

  const finish = useCallback(async () => {
    await markOnboardingSeen();
    router.replace('/');
  }, [router]);

  const onScroll = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      const next = Math.round(event.nativeEvent.contentOffset.x / width);
      if (next !== index) setIndex(next);
    },
    [index, width],
  );

  const advance = async () => {
    if (!last) {
      scroller.current?.scrollTo({ x: width * (index + 1), animated: true });
      return;
    }
    // Asking here rather than on a cold feed means the system dialog arrives
    // with a reason already on screen. A refusal is not a dead end: the feed
    // explains itself, so onboarding finishes either way.
    setBusy(true);
    try {
      await location.current();
    } catch {
      // Declined or unavailable; the feed handles saying so.
    } finally {
      setBusy(false);
      await finish();
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: tone.bg }}>
      <SafeAreaView edges={['top']}>
        <View style={styles.top}>
          {!last && (
            <Pressable onPress={finish} hitSlop={10}>
              <Text style={[t.meta(12, '600', 0.3), { color: tone.chalk }]}>Skip</Text>
            </Pressable>
          )}
        </View>
      </SafeAreaView>

      <ScrollView
        ref={scroller}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onScroll={onScroll}
        scrollEventThrottle={16}
        style={{ flex: 1 }}>
        {SLIDES.map((slide) => (
          <View key={slide.key} style={[styles.slide, { width }]}>
            <View style={styles.art}>{slide.art()}</View>
            <Text style={[t.display(29, '700'), { color: tone.ink }]}>{slide.title}</Text>
            <Text style={[t.body(16), { color: tone.chalk, marginTop: 12 }]}>
              {slide.body}
            </Text>
          </View>
        ))}
      </ScrollView>

      <SafeAreaView edges={['bottom']}>
        <View style={styles.bottom}>
          <View style={styles.dots}>
            {SLIDES.map((slide, i) => (
              <View
                key={slide.key}
                style={[
                  styles.dot,
                  {
                    backgroundColor: i === index ? tone.accent : `${tone.ink}22`,
                    width: i === index ? 20 : 7,
                  },
                ]}
              />
            ))}
          </View>

          <Pressable
            onPress={advance}
            disabled={busy}
            style={[styles.cta, { backgroundColor: tone.accent, opacity: busy ? 0.6 : 1 }]}>
            <Text style={[t.display(16, '600'), { color: '#000' }]}>
              {last ? (busy ? 'One moment…' : 'Enable location') : 'Next'}
            </Text>
          </Pressable>

          {last && (
            <Pressable onPress={finish} hitSlop={8} style={styles.later}>
              <Text style={[t.meta(12, '600', 0.3), { color: tone.chalk }]}>Not now</Text>
            </Pressable>
          )}
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  top: {
    height: 40, paddingHorizontal: metric.gutter,
    alignItems: 'flex-end', justifyContent: 'center',
  },
  slide: { paddingHorizontal: metric.gutter, justifyContent: 'center' },
  art: { height: 210, alignItems: 'center', justifyContent: 'center', marginBottom: 34 },
  bottom: { paddingHorizontal: metric.gutter, paddingBottom: 8 },
  dots: { flexDirection: 'row', justifyContent: 'center', marginBottom: 22 },
  dot: { height: 7, borderRadius: 4, marginHorizontal: 3 },
  cta: {
    height: 52, borderRadius: metric.radius,
    alignItems: 'center', justifyContent: 'center',
  },
  later: { alignItems: 'center', paddingVertical: 14 },
});
