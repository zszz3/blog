export type ArticleView = 'blog' | 'docs'

interface Article {
  id: string
  data: {
    views: ArticleView[]
    draft: boolean
    publishDate: Date
    series?: string
    order: number
  }
}

export function articleUrl(article: Pick<Article, 'id'>) {
  return `/blog/${article.id}`
}

export function selectArticles<T extends Article>(articles: T[], view?: ArticleView, includeDrafts = false): T[] {
  return articles.filter(article => (includeDrafts || !article.data.draft) && (!view || article.data.views.includes(view)))
    .sort((a, b) => b.data.publishDate.valueOf() - a.data.publishDate.valueOf() || a.id.localeCompare(b.id))
}

export function groupDocs<T extends Article>(articles: T[]): [string, T[]][] {
  const groups = new Map<string, T[]>()
  for (const article of articles.filter(article => article.data.views.includes('docs'))) {
    const name = article.data.series || '其他文档'
    const group = groups.get(name) || []
    group.push(article)
    groups.set(name, group)
  }
  return [...groups].sort(([a], [b]) => a.localeCompare(b, 'zh-CN')).map(([name, entries]) => [
    name, entries.sort((a, b) => a.data.order - b.data.order || a.data.publishDate.valueOf() - b.data.publishDate.valueOf() || a.id.localeCompare(b.id))
  ])
}

export function groupArticlesByYear<T extends Article>(articles: T[]): [number, T[]][] {
  const groups = new Map<number, T[]>()
  for (const article of articles) {
    const year = article.data.publishDate.getUTCFullYear()
    groups.set(year, [...(groups.get(year) || []), article])
  }
  return [...groups].sort(([a], [b]) => b - a)
}
