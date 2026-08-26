import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import type { GeoPoint } from '../domain/issue';
import { useServices } from './context';

const key = (point: GeoPoint) => ['nearby', point.latitude, point.longitude] as const;

/** The repository's opaque cursor maps straight onto useInfiniteQuery. */
export function useNearbyFeed(point: GeoPoint) {
  const { issues } = useServices();
  return useInfiniteQuery({
    queryKey: key(point),
    initialPageParam: null as string | null,
    queryFn: ({ pageParam }) => issues.nearby({ point, cursor: pageParam }),
    getNextPageParam: (last) => last.next_cursor,
  });
}

export function useMapIssues(point: GeoPoint) {
  const { issues } = useServices();
  return useQuery({
    queryKey: ['map', point.latitude, point.longitude],
    queryFn: () => issues.nearby({ point, limit: 200 }),
  });
}

export function useIssue(id: string) {
  const { issues } = useServices();
  return useQuery({ queryKey: ['issue', id], queryFn: () => issues.get(id) });
}

export function useLocation() {
  const { location } = useServices();
  return useQuery({ queryKey: ['location'], queryFn: () => location.current(), retry: false });
}

export function useConfirm() {
  const { issues } = useServices();
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, confirmed }: { id: string; confirmed: boolean }) =>
      confirmed ? issues.unconfirm(id) : issues.confirm(id),
    onSuccess: (updated) => {
      client.setQueryData(['issue', updated.id], updated);
      client.invalidateQueries({ queryKey: ['nearby'] });
    },
  });
}
