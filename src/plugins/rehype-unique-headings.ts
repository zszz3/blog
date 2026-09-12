import type { Root } from 'hast'
import { visit } from 'unist-util-visit'
export default function uniqueHeadings() {
  return (tree: Root) => {
    const used = new Set<string>()
    visit(tree, 'element', node => {
      if (!/^h[1-6]$/.test(node.tagName) || !node.properties.id) return
      const original = String(node.properties.id)
      let id = original, suffix = 1
      while (used.has(id)) id = `${original}-${suffix++}`
      used.add(id)
      node.properties.id = id
    })
  }
}
