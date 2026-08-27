import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from 'react';
import type { NativeScrollEvent, NativeSyntheticEvent } from 'react-native';

type Chrome = {
  /** Masthead, section tabs and dock. The FAB is deliberately not part of it. */
  visible: boolean;
  show: () => void;
  hide: () => void;
};

const ChromeContext = createContext<Chrome | null>(null);

export function ChromeProvider({ children }: { children: React.ReactNode }) {
  const [visible, setVisible] = useState(true);
  const value = useMemo(
    () => ({
      visible,
      show: () => setVisible(true),
      hide: () => setVisible(false),
    }),
    [visible],
  );
  return <ChromeContext.Provider value={value}>{children}</ChromeContext.Provider>;
}

export function useChrome(): Chrome {
  const chrome = useContext(ChromeContext);
  if (!chrome) throw new Error('useChrome must be used inside ChromeProvider');
  return chrome;
}

/** Ignore the rubber-band overscroll at the ends, which otherwise reads as a
 *  direction change and flickers the dock. */
const THRESHOLD = 8;

/**
 * Scroll-driven chrome for any list. Reading hides it, coming back up or
 * reaching the top restores it — so the dock is always one upward flick away
 * and the user can never be stranded in fullscreen.
 *
 * Spread onto a FlatList or ScrollView: `{...useChromeOnScroll()}`.
 */
export function useChromeOnScroll() {
  const { show, hide } = useChrome();
  const last = useRef(0);

  const onScroll = useCallback(
    (event: NativeSyntheticEvent<NativeScrollEvent>) => {
      const y = event.nativeEvent.contentOffset.y;
      if (Math.abs(y - last.current) <= THRESHOLD) return;
      if (y < last.current || y <= 0) show();
      else hide();
      last.current = y;
    },
    [hide, show],
  );

  return { onScroll, scrollEventThrottle: 16 } as const;
}
