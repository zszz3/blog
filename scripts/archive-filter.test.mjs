import assert from 'node:assert/strict'
import { test } from 'node:test'
import { archiveFilterUrl, matchesArchiveFilter, readArchiveFilter } from '../src/utils/archive-filter.ts'

const entries = [
  { id: 'java', tags: ['Java', '八股'], category: '八股' },
  { id: 'mysql', tags: ['MySQL', '八股'], category: '八股' },
  { id: 'guide', tags: ['Blogging'], category: 'Guides' },
  { id: 'javascript', tags: ['JavaScript'], category: '未分类' }
]
const select = filter => entries.filter(entry => matchesArchiveFilter(entry, filter)).map(entry => entry.id)

test('tag selection matches whole tags and includes every matching article', () => {
  assert.deepEqual(select({ tag: '八股', category: '' }), ['java', 'mysql'])
  assert.deepEqual(select({ tag: 'Java', category: '' }), ['java'])
})

test('category and tag intersect, including an empty result and a complete reset', () => {
  assert.deepEqual(select({ tag: '', category: '八股' }), ['java', 'mysql'])
  assert.deepEqual(select({ tag: 'Java', category: '八股' }), ['java'])
  assert.deepEqual(select({ tag: 'Java', category: 'Guides' }), [])
  assert.equal(select({ tag: '', category: '' }).length, entries.length)
})

test('Chinese and plus signs survive shareable URLs and unrelated URL state is preserved', () => {
  const original = new URL('https://example.com/archives?from=home#articles')
  const filter = { tag: 'C++', category: '八股' }
  const path = archiveFilterUrl(original, filter)
  const shared = new URL(path, original)
  assert.deepEqual(readArchiveFilter(shared.search, ['C++'], ['八股']), filter)
  assert.equal(shared.searchParams.get('from'), 'home')
  assert.equal(shared.hash, '#articles')
  assert.equal(original.search, '?from=home')
  assert.equal(archiveFilterUrl(shared, { tag: '', category: '' }), '/archives?from=home#articles')
})

test('unknown or removed filters fall back to an available selection', () => {
  assert.deepEqual(readArchiveFilter('?tag=removed&category=八股', ['Java'], ['八股']), { tag: '', category: '八股' })
  assert.deepEqual(readArchiveFilter('?category=removed', ['Java'], ['八股']), { tag: '', category: '' })
})
