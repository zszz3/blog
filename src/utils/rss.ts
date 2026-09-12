import type { APIContext, ImageMetadata } from 'astro'
import path from 'node:path'
import { getImage } from 'astro:assets'
import type { CollectionEntry } from 'astro:content'
import rss from '@astrojs/rss'
import type { Root } from 'mdast'
import rehypeStringify from 'rehype-stringify'
import remarkParse from 'remark-parse'
import remarkRehype from 'remark-rehype'
import { unified } from 'unified'
import { visit } from 'unist-util-visit'
import config from 'virtual:config'

import { articleUrl, getArticles } from './articles'
import type { ArticleView } from './article-model'

// Get dynamic import of images as a map collection
const imagesGlob = import.meta.glob<{ default: ImageMetadata }>(
  '/src/**/*.{jpeg,jpg,png,gif,avif,webp,svg}' // add more image formats if needed
)

const renderContent = async (post: CollectionEntry<'blog'>, site: URL) => {
  // Replace image links with the correct path
  function remarkReplaceImageLink() {
    /**
     * @param {Root} tree
     */
    return async (tree: Root) => {
      const promises: Promise<void>[] = []
      visit(tree, 'image', (node) => {
        if (node.url.startsWith('/')) {
          node.url = new URL(node.url, site).href
        } else {
          if (/^(https?:|data:)/i.test(node.url)) return
          const imagePathPrefix = '/' + path.posix.normalize(path.posix.join(path.posix.dirname(post.filePath!), decodeURIComponent(node.url)))
          const promise = imagesGlob[imagePathPrefix]?.().then(async (res) => {
            const imagePath = res?.default
            if (imagePath) {
              node.url = `${site}${(await getImage({ src: imagePath })).src.replace('/', '')}`
            }
          })
          if (promise) promises.push(promise)
        }
      })
      await Promise.all(promises)
    }
  }

  const file = await unified()
    .use(remarkParse)
    .use(remarkReplaceImageLink)
    .use(remarkRehype)
    .use(rehypeStringify)
    .process(post.body)

  return String(file)
}

export const createArticleFeed = async (context: APIContext, view?: ArticleView) => {
  const allPostsByDate = await getArticles(view, false)
  const siteUrl = context.site ?? new URL(import.meta.env.SITE)

  return rss({
    // Basic configs
    trailingSlash: false,
    xmlns: { h: 'http://www.w3.org/TR/html4/', atom: 'http://www.w3.org/2005/Atom' },
    stylesheet: '/scripts/pretty-feed-v3.xsl',

    // Contents
    title: view === 'docs' ? `${config.title} · 文档` : config.title,
    description: config.description,
    site: import.meta.env.SITE,
    items: await Promise.all(
      allPostsByDate.map(async (post) => ({
        pubDate: post.data.publishDate,
        link: articleUrl(post),
        // `pubDate` intentionally stays on `publishDate` so aggregators do not re-flow an
        // edited post as new. `atom:updated` lets readers that support it detect the edit.
        customData: post.data.updatedDate ? `<atom:updated>${post.data.updatedDate.toISOString()}</atom:updated>` : '',
        content: await renderContent(post, siteUrl),
        title: post.data.title,
        description: post.data.description,
        categories: post.data.tags
      }))
    )
  })
}
