#!/usr/bin/env node
import { mkdir, writeFile, access } from 'node:fs/promises'
import path from 'node:path'
import { parseArgs } from 'node:util'
const {values,positionals}=parseArgs({allowPositionals:true,options:{slug:{type:'string'}}})
const title=positionals[0]
if(!title){console.error('用法：pnpm new-post "文章标题" --slug article-name');process.exit(1)}
const slug=values.slug || title.normalize('NFKC').trim().toLowerCase().replace(/\s+/g,'-')
if(!/^[\p{L}\p{N}][\p{L}\p{N}_-]{0,99}$/u.test(slug)){console.error('文章目录只能包含文字、数字、横线和下划线。');process.exit(1)}
const dir=path.resolve('src/content/posts',slug),target=path.join(dir,'index.md')
try{await access(dir);throw new Error('目录已经存在，请使用新的 slug。')}catch(error){if(error.code!=='ENOENT')throw error}
await mkdir(dir,{recursive:true})
const date=new Date().toLocaleDateString('en-CA',{timeZone:'Asia/Shanghai'})
await writeFile(target,`---\ntitle: ${JSON.stringify(title)}\npublished: ${date}\ndescription: ""\nimage: ""\ntags: []\ncategory: ""\ndraft: true\n---\n\n在这里开始写作。\n`,{flag:'wx'})
console.log(`已创建草稿：${path.relative(process.cwd(),target)}\n写完后把 draft 改为 false，再提交到 main 发布。`)
