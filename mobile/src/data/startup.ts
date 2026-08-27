import AsyncStorage from '@react-native-async-storage/async-storage';

const SEEN_KEY = 'fihy.onboarded';

/** Not secret and not worth a keychain round trip, unlike the tokens. */
export async function hasSeenOnboarding(): Promise<boolean> {
  try {
    return (await AsyncStorage.getItem(SEEN_KEY)) === 'true';
  } catch {
    // A device that cannot read this is better off seeing the intro twice
    // than being stuck behind a storage error on first launch.
    return false;
  }
}

export async function markOnboardingSeen(): Promise<void> {
  try {
    await AsyncStorage.setItem(SEEN_KEY, 'true');
  } catch {
    // Losing the flag costs one repeated intro, so it is not worth failing on.
  }
}

export async function forgetOnboarding(): Promise<void> {
  try {
    await AsyncStorage.removeItem(SEEN_KEY);
  } catch {}
}
