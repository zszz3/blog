import { defineCollection } from 'astro:content'
import { glob } from 'astro/loaders'
import { z } from 'astro/zod'

// One article collection for both views. Keep the historical `blog` key and URLs
// for Astro Pure compatibility; `views` controls where an article is listed.
const blog = defineCollection({
  loader: glob({
    base: './src/content/posts', pattern: '**/*.{md,mdx}',
    generateId: ({ entry }) => entry.replace(/\.(md|mdx)$/i, '').replace(/\/index$/, '').toLowerCase()
  }),
  schema: ({ image }) => z.object({
    title: z.string().min(1), description: z.string().default(''),
    published: z.coerce.date().optional(), publishDate: z.coerce.date().optional(),
    updated: z.coerce.date().optional(), updatedDate: z.coerce.date().optional(),
    image: z.preprocess(value => value === '' ? undefined : value, image().optional()),
    heroImage: z.object({ src: image(), alt: z.string().optional(), color: z.string().optional() }).optional(),
    tags: z.array(z.string()).default([]), category: z.string().nullable().optional(),
    lang: z.string().optional(), language: z.string().optional(),
    draft: z.boolean().default(false), comment: z.boolean().default(false),
    views: z.array(z.enum(['blog', 'docs'])).min(1).default(['blog'])
      .transform(views => [...new Set(views)]),
    series: z.string().trim().min(1).optional(),
    order: z.number().int().nonnegative().default(999)
  }).refine(data => data.publishDate || data.published, '请填写 published 或 publishDate')
    .transform(data => ({
      ...data, publishDate: (data.publishDate || data.published)!,
      updatedDate: data.updatedDate || data.updated,
      heroImage: data.heroImage || (data.image ? { src: data.image, alt: data.title } : undefined),
      category: data.category?.trim() || '未分类',
      language: data.language || data.lang || 'zh-CN'
    }))
})
export const collections = { blog }
