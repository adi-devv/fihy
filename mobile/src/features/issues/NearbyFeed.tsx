import { useRouter } from 'expo-router';
import React, { useCallback, useMemo } from 'react';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { useConfirm, useNearbyFeed } from '../../data/queries';
import { useServices } from '../../data/context';
import type { GeoPoint, Issue } from '../../domain/issue';
import { metric, type as t, useTone } from '../../theme/tokens';
import { IssueCard } from './IssueCard';

export function NearbyFeed({
  point,
  onScrollDirection,
}: {
  point: GeoPoint;
  onScrollDirection: (visible: boolean) => void;
}) {
  const tone = useTone();
  const router = useRouter();
  const { auth } = useServices();
  const confirm = useConfirm();
  const feed = useNearbyFeed(point);
  const lastOffset = React.useRef(0);

  const issues = useMemo(
    () => feed.data?.pages.flatMap((p) => p.items) ?? [],
    [feed.data],
  );

  const onScroll = useCallback(
    (event: { nativeEvent: { contentOffset: { y: number } } }) => {
      const y = event.nativeEvent.contentOffset.y;
      if (Math.abs(y - lastOffset.current) > 8) {
        onScrollDirection(y < lastOffset.current || y <= 0);
        lastOffset.current = y;
      }
    },
    [onScrollDirection],
  );

  const onConfirm = useCallback(
    (issue: Issue) => {
      if (!auth.currentUserId()) {
        router.push('/auth');
        return;
      }
      confirm.mutate({ id: issue.id, confirmed: issue.confirmed_by_me });
    },
    [auth, confirm, router],
  );

  if (feed.isPending) return <Centered><ActivityIndicator color={tone.accentDeep} /></Centered>;
  if (feed.isError) return <Notice text={`Could not load issues: ${(feed.error as Error).message}`} />;
  if (!issues.length) {
    return <Notice text="Nothing reported near you yet. Tap plus to be the first." />;
  }

  return (
    <FlatList
      data={issues}
      keyExtractor={(issue) => issue.id}
      onScroll={onScroll}
      scrollEventThrottle={16}
      contentContainerStyle={{ paddingBottom: 96 }}
      onEndReachedThreshold={0.6}
      onEndReached={() => feed.hasNextPage && !feed.isFetchingNextPage && feed.fetchNextPage()}
      refreshControl={
        <RefreshControl refreshing={feed.isRefetching} onRefresh={feed.refetch} tintColor={tone.accentDeep} />
      }
      ListFooterComponent={
        feed.isFetchingNextPage ? (
          <View style={{ paddingVertical: 26 }}>
            <ActivityIndicator color={tone.accentDeep} />
          </View>
        ) : null
      }
      renderItem={({ item }) => (
        <IssueCard
          issue={item}
          onPress={() => router.push(`/issues/${item.id}`)}
          onConfirm={() => onConfirm(item)}
        />
      )}
    />
  );
}

export const Centered = ({ children }: { children: React.ReactNode }) => (
  <View style={styles.centered}>{children}</View>
);

export function Notice({ text }: { text: string }) {
  const tone = useTone();
  return (
    <View style={styles.centered}>
      <Text style={[t.body(15), { color: tone.chalk, textAlign: 'center', padding: 28 }]}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  centered: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: metric.gutter },
});
