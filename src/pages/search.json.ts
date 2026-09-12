import { getCollection } from 'astro:content'
export async function GET() {
  const [posts,docs] = await Promise.all([getCollection('blog'),getCollection('docs')])
  const index = [...posts,...docs].filter(post=>!post.data.draft).map(post=>({
    title:post.data.title,description:post.data.description,body:post.body||'',
    url:`/${post.collection==='blog'?'blog':'docs'}/${post.id}`,
    kind:post.collection,category:post.collection==='blog'?post.data.category:'文档',
    tags:post.data.tags,date:post.data.publishDate?.toISOString().slice(0,10)||''
  }))
  return new Response(JSON.stringify(index),{headers:{'Content-Type':'application/json; charset=utf-8'}})
}
