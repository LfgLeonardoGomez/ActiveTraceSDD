// ── Pagination envelope helpers ──
// Several list endpoints return a paginated envelope ({ items, total, limit,
// offset }) while others return a bare array. Components expect an array, so
// `.map()` on the envelope throws and unmounts the whole tree. `toList`
// normalises both shapes into a plain array.

export interface Paginated<T> {
  items: T[];
  total?: number;
  limit?: number;
  offset?: number;
}

export function toList<T>(data: T[] | Paginated<T> | null | undefined): T[] {
  if (Array.isArray(data)) return data;
  return data?.items ?? [];
}
