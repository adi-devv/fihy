import { Redirect } from 'expo-router';
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, View } from 'react-native';
import { useServices } from '../src/data/context';
import { hasSeenOnboarding } from '../src/data/startup';
import { HomeShell } from '../src/features/shell/HomeShell';
import { useTone } from '../src/theme/tokens';

type Gate = 'checking' | 'onboarding' | 'ready';

/**
 * Cold start: reload any stored session, then decide whether the intro is
 * owed. Both have to settle before the shell mounts, or a returning user sees
 * themselves signed out and the feed asks for location with no reason given.
 */
export default function Home() {
  const tone = useTone();
  const { auth } = useServices();
  const [gate, setGate] = useState<Gate>('checking');

  useEffect(() => {
    let live = true;
    (async () => {
      try {
        await auth.restore();
      } catch {
        // A session that will not reload just means signed out.
      }
      const seen = await hasSeenOnboarding();
      if (live) setGate(seen ? 'ready' : 'onboarding');
    })();
    return () => {
      live = false;
    };
  }, [auth]);

  if (gate === 'checking') {
    return (
      <View style={{ flex: 1, backgroundColor: tone.bg, justifyContent: 'center' }}>
        <ActivityIndicator color={tone.accentDeep} />
      </View>
    );
  }
  if (gate === 'onboarding') return <Redirect href="/onboarding" />;
  return <HomeShell />;
}
