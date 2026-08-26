import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { useColorScheme } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { ServicesProvider } from '../src/data/context';
import { useTone } from '../src/theme/tokens';

const client = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 30_000 } },
});

export default function RootLayout() {
  const scheme = useColorScheme();
  return (
    <SafeAreaProvider>
      <QueryClientProvider client={client}>
        <ServicesProvider>
          <StatusBar style={scheme === 'dark' ? 'light' : 'dark'} />
          <Routes />
        </ServicesProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}

function Routes() {
  const tone = useTone();
  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: tone.bg },
        headerTintColor: tone.ink,
        headerShadowVisible: false,
        contentStyle: { backgroundColor: tone.bg },
      }}>
      <Stack.Screen name="index" options={{ headerShown: false }} />
      <Stack.Screen name="auth" options={{ title: 'Sign in' }} />
      <Stack.Screen name="report" options={{ headerShown: false, presentation: 'modal' }} />
      <Stack.Screen name="issues/[id]" options={{ title: '' }} />
    </Stack>
  );
}
