import { articleUrl, getArticles } from '@/utils/articles'
export async function GET() {
  const index = (await getArticles(undefined, false)).map(post=>({
    title:post.data.title,description:post.data.description,body:post.body||'',
    url:articleUrl(post),
    views:post.data.views,category:post.data.category,
    tags:post.data.tags,date:post.data.publishDate?.toISOString().slice(0,10)||''
  }))
  return new Response(JSON.stringify(index),{headers:{'Content-Type':'application/json; charset=utf-8'}})
}
