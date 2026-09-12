import assert from 'node:assert/strict'
import { test } from 'node:test'
import { articleUrl, selectArticles, groupDocs, groupArticlesByYear } from '../src/utils/article-model.ts'

const article = (id, views, extra = {}) => ({ id, data: {
  views, draft: false, publishDate: new Date('2025-01-01'), order: 999, ...extra
} })
const dual = article('mysql/locks', ['blog', 'docs'], { series: 'MySQL', order: 2 })
const blog = article('diary', ['blog'])
const doc = article('mysql/intro', ['docs'], { series: 'MySQL', order: 1 })
const draft = article('unpublished', ['blog', 'docs'], { draft: true })
const source = [dual, blog, doc, draft]

test('each view selects the same source records, and the all-content view is unique', () => {
  assert.deepEqual(new Set(selectArticles(source, 'blog')), new Set([dual, blog]))
  assert.deepEqual(new Set(selectArticles(source, 'docs')), new Set([dual, doc]))
  assert.equal(selectArticles(source).length, 3)
  assert.equal(selectArticles(source, 'blog').find(item => item.id === dual.id),
    selectArticles(source, 'docs').find(item => item.id === dual.id))
})

test('drafts are excluded by default and can be previewed explicitly', () => {
  for (const view of [undefined, 'blog', 'docs']) assert.ok(!selectArticles(source, view).includes(draft))
  assert.ok(selectArticles(source, 'docs', true).includes(draft))
})

test('series chapters use order; other series and blog-only articles cannot leak in', () => {
  const grouped = groupDocs(selectArticles([...source, article('java', ['docs'], { series: 'Java' }), article('loose', ['docs'])]))
  assert.deepEqual(grouped.find(([name]) => name === 'MySQL')[1].map(item => item.id), ['mysql/intro', 'mysql/locks'])
  assert.equal(grouped.find(([name]) => name === '其他文档')[1][0].id, 'loose')
  assert.ok(!grouped.flatMap(([, items]) => items).includes(blog))
  assert.deepEqual(source, [dual, blog, doc, draft])
})

test('changing title, views, series or chapter position preserves the article URL', () => {
  assert.equal(articleUrl(dual), articleUrl({ ...dual, data: { ...dual.data, title: 'Renamed', views: ['docs'], series: 'New', order: 10 } }))
})

test('blog and archive use publication date even after an old article is edited', () => {
  const old = article('old', ['blog'], { publishDate: new Date('2023-01-01'), updatedDate: new Date('2027-01-01') })
  const recent = article('recent', ['blog'], { publishDate: new Date('2026-01-01') })
  const result = selectArticles([old, recent], 'blog')
  assert.deepEqual(result.map(item => item.id), ['recent', 'old'])
  assert.deepEqual(groupArticlesByYear(result).map(([year]) => year), [2026, 2023])
})
