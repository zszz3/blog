export interface ArchiveFilter {
  tag: string
  category: string
}

export interface ArchiveEntry {
  tags: readonly string[]
  category: string
}

export function matchesArchiveFilter(entry: ArchiveEntry, filter: ArchiveFilter) {
  return (!filter.tag || entry.tags.includes(filter.tag))
    && (!filter.category || entry.category === filter.category)
}

export function readArchiveFilter(search: string, tags: readonly string[], categories: readonly string[]): ArchiveFilter {
  const params = new URLSearchParams(search)
  const tag = params.get('tag') || ''
  const category = params.get('category') || ''
  return {
    tag: tags.includes(tag) ? tag : '',
    category: categories.includes(category) ? category : ''
  }
}

export function archiveFilterUrl(url: URL, filter: ArchiveFilter) {
  const next = new URL(url)
  for (const key of ['tag', 'category'] as const) {
    if (filter[key]) next.searchParams.set(key, filter[key])
    else next.searchParams.delete(key)
  }
  return `${next.pathname}${next.search}${next.hash}`
}
