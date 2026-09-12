import type { APIContext } from 'astro'
import { createArticleFeed } from '@/utils/rss'
export const GET = (context: APIContext) => createArticleFeed(context, 'docs')
