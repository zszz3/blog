import { getCollection } from 'astro:content'
import { selectArticles, type ArticleView } from './article-model'

export { articleUrl, groupDocs, groupArticlesByYear } from './article-model'

export async function getArticles(view?: ArticleView, includeDrafts = import.meta.env.DEV) {
  return selectArticles(await getCollection('blog'), view, includeDrafts)
}
