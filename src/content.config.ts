import { defineCollection } from 'astro:content'
import { glob } from 'astro/loaders'
import { z } from 'astro/zod'

// Read the original article directory and front matter without rewriting the user's files.
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
    draft: z.boolean().default(false), comment: z.boolean().default(false)
  }).refine(data => data.publishDate || data.published, '请填写 published 或 publishDate')
    .transform(data => ({
      ...data, publishDate: (data.publishDate || data.published)!,
      updatedDate: data.updatedDate || data.updated,
      heroImage: data.heroImage || (data.image ? { src: data.image, alt: data.title } : undefined),
      category: data.category?.trim() || '未分类',
      language: data.language || data.lang || 'zh-CN'
    }))
})
const docs = defineCollection({
  loader: glob({ base: './src/content/docs', pattern: '**/*.{md,mdx}' }),
  schema: () => z.object({
    title: z.string(), description: z.string().default(''),
    publishDate: z.coerce.date().optional(), updatedDate: z.coerce.date().optional(),
    tags: z.array(z.string()).default([]), draft: z.boolean().default(false), order: z.number().default(999)
  })
})
export const collections = { blog, docs }
