import { archiveFilterUrl, matchesArchiveFilter, readArchiveFilter } from './archive-filter'

const root = document.querySelector<HTMLElement>('#archive-browser')

if (root) {
  const controls = root.querySelector<HTMLFormElement>('#archive-filters')!
  const categorySelect = root.querySelector<HTMLSelectElement>('#archive-category')!
  const tagButtons = [...root.querySelectorAll<HTMLButtonElement>('[data-archive-tag]')]
  const reset = root.querySelector<HTMLButtonElement>('#archive-reset')!
  const status = root.querySelector<HTMLElement>('#archive-status')!
  const empty = root.querySelector<HTMLElement>('#archive-empty')!
  const groups = [...root.querySelectorAll<HTMLElement>('[data-archive-year]')]
  const entries = [...root.querySelectorAll<HTMLElement>('[data-archive-entry]')].map(element => ({
    element,
    data: {
      tags: JSON.parse(element.dataset.tags || '[]') as string[],
      category: element.dataset.category || ''
    }
  }))
  const tags = tagButtons.map(button => button.dataset.archiveTag || '')
  const categories = [...categorySelect.options].map(option => option.value)
  let filter = readArchiveFilter(location.search, tags, categories)

  function render(updateHistory = false) {
    let count = 0
    for (const entry of entries) {
      const visible = matchesArchiveFilter(entry.data, filter)
      entry.element.hidden = !visible
      if (visible) count++
    }
    for (const group of groups) {
      const visibleCount = group.querySelectorAll('[data-archive-entry]:not([hidden])').length
      group.hidden = visibleCount === 0
      group.querySelector<HTMLElement>('[data-year-count]')!.textContent = `${visibleCount} 篇`
    }
    for (const button of tagButtons) {
      button.setAttribute('aria-pressed', String(button.dataset.archiveTag === filter.tag))
    }
    categorySelect.value = filter.category
    reset.hidden = !filter.tag && !filter.category
    status.textContent = `共 ${count} 篇文章`
    empty.hidden = count > 0
    if (updateHistory) {
      const url = archiveFilterUrl(new URL(location.href), filter)
      if (url !== `${location.pathname}${location.search}${location.hash}`) history.pushState(null, '', url)
    }
  }

  controls.hidden = false
  controls.addEventListener('submit', event => event.preventDefault())
  tagButtons.forEach(button => button.addEventListener('click', () => {
    filter.tag = button.dataset.archiveTag || ''
    render(true)
  }))
  categorySelect.addEventListener('change', () => {
    filter.category = categorySelect.value
    render(true)
  })
  reset.addEventListener('click', () => {
    filter = { tag: '', category: '' }
    render(true)
  })
  window.addEventListener('popstate', () => {
    filter = readArchiveFilter(location.search, tags, categories)
    render()
  })
  render()
}
