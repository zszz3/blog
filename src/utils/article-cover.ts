import type { ImageMetadata } from 'astro'
import type { CollectionEntry } from 'astro:content'
import path from 'node:path'
import remarkParse from 'remark-parse'
import { unified } from 'unified'
import { visit } from 'unist-util-visit'

type ImageImports = Record<string, () => Promise<{ default: ImageMetadata }>>
type Cover = { src: ImageMetadata } | { src: string }

export async function getArticleCover(post: CollectionEntry<'blog'>, images: ImageImports): Promise<Cover | undefined> {
  if (post.data.heroImage) return { src: post.data.heroImage.src }

  const tree = unified().use(remarkParse).parse(post.body || '')
  const definitions = new Map<string, string>()
  visit(tree, 'definition', node => { definitions.set(node.identifier, node.url) })

  let source: string | undefined
  visit(tree, node => {
    if (source) return
    if (node.type === 'image') source = node.url
    if (node.type === 'imageReference') source = definitions.get(node.identifier)
  })
  if (!source) return
  if (/^https?:\/\//i.test(source) || /^\/(?!\/)/.test(source)) return { src: source }
  if (!post.filePath || /^[a-z][a-z\d+.-]*:/i.test(source) || source.startsWith('//')) return

  let filename: string
  try {
    filename = decodeURIComponent(source.split(/[?#]/, 1)[0])
  } catch {
    return
  }
  const imagePath = path.posix.resolve('/', path.posix.dirname(post.filePath), filename)
  const image = await images[imagePath]?.()
  return image ? { src: image.default } : undefined
}
