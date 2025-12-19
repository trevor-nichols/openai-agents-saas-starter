export type CursorPage<TItem> = {
  items?: TItem[] | null;
  next_cursor?: string | null;
};

export type CursorPaginationOptions = {
  maxPages?: number;
};

const DEFAULT_MAX_PAGES = 100;

/**
 * Collect all items from a cursor-paginated endpoint.
 *
 * Throws if pagination exceeds `maxPages` to avoid silently truncating results.
 */
export async function collectCursorItems<TItem>(
  fetchPage: (cursor: string | null) => Promise<CursorPage<TItem>>,
  options: CursorPaginationOptions = {},
): Promise<TItem[]> {
  const maxPages = options.maxPages ?? DEFAULT_MAX_PAGES;
  const items: TItem[] = [];
  let cursor: string | null = null;

  for (let pageIdx = 0; pageIdx < maxPages; pageIdx += 1) {
    const page = await fetchPage(cursor);
    items.push(...(page.items ?? []));
    cursor = page.next_cursor ?? null;
    if (!cursor) {
      return items;
    }
  }

  throw new Error(
    `Pagination exceeded ${maxPages} pages; increase maxPages to fetch all items.`,
  );
}

export { DEFAULT_MAX_PAGES };
