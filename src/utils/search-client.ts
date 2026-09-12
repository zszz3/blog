interface ResultData { url: string; excerpt: string; meta: {title?:string;date?:string;category?:string;kind?:string}; sub_results?: {url:string;title:string;excerpt:string}[] }
interface Result { data: () => Promise<ResultData> }
interface Engine { options: (options:object) => Promise<void>; search: (query:string|null, options:object) => Promise<{results:Result[]}> }
interface FallbackEntry {title:string;description:string;url:string;body:string;tags:string[];category:string;date:string;views:('blog'|'docs')[]}
const form = document.querySelector<HTMLFormElement>('#search-form')!
const input = document.querySelector<HTMLInputElement>('#search-input')!
const status = document.querySelector<HTMLElement>('#search-status')!
const results = document.querySelector<HTMLElement>('#search-results')!
const more = document.querySelector<HTMLButtonElement>('#search-more')!
const suggestions = document.querySelector<HTMLElement>('#search-suggestions')!
const keys = ['kind','category','tag','year','sort'] as const
const selectors = Object.fromEntries(keys.map(key => [key,document.querySelector<HTMLSelectElement>(`#search-${key}`)!])) as Record<typeof keys[number], HTMLSelectElement>
let enginePromise: Promise<Engine|null> | undefined
let fallbackPromise: Promise<FallbackEntry[]> | undefined
let generation = 0, shown = 0
let matches: Result[] = []
let timer: ReturnType<typeof setTimeout>
let composing = false
function normalized(value:string) {return value.normalize('NFKC').toLocaleLowerCase().trim()}
function escape(value:string) {return value.replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]!))}
function markup(value:string, query:string) {
  const words = query.split(/\s+/).filter(Boolean).sort((a,b) => b.length-a.length)
  if(!words.length) return escape(value)
  const pattern = new RegExp(words.map(word => word.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|'),'gi')
  let output='', end=0
  for(const match of value.matchAll(pattern)) {output+=escape(value.slice(end,match.index))+'<mark>'+escape(match[0])+'</mark>';end=match.index!+match[0].length}
  return output+escape(value.slice(end))
}
function safeHighlight(element:HTMLElement, html:string) {
  // Only copy text and highlights from an excerpt, never executable markup or attributes.
  const parsed = new DOMParser().parseFromString(html,'text/html')
  const append = (parent:Node, node:Node) => {
    if(node.nodeType === Node.TEXT_NODE) parent.appendChild(document.createTextNode(node.textContent || ''))
    else if(node instanceof Element) {
      if(node.tagName === 'MARK') {const mark=document.createElement('mark');mark.textContent=node.textContent;parent.appendChild(mark)}
      else node.childNodes.forEach(child => append(parent,child))
    }
  }
  parsed.body.childNodes.forEach(node => append(element,node))
}
function siteUrl(value:string) {const parsed=new URL(value,location.origin);return parsed.origin === location.origin ? (parsed.pathname.replace(/\/$/,'') || '/')+parsed.search+parsed.hash : '/blog'}
async function getEngine() {
  if(import.meta.env.DEV) return null
  const moduleUrl = '/pagefind/pagefind.js'
  enginePromise ||= import(/* @vite-ignore */ moduleUrl).then(async engine => {await engine.options({excerptLength:36});return engine}).catch(() => null)
  return enginePromise
}
async function fallbackSearch(query:string, filters:Record<string,string>, newest:boolean):Promise<Result[]> {
  fallbackPromise ||= fetch('/search.json').then(r => {if(!r.ok) throw new Error('Search index unavailable');return r.json()})
  const terms=normalized(query).split(/\s+/).filter(Boolean)
  const ranked=(await fallbackPromise).flatMap(entry => {
    if(Object.entries(filters).some(([key,value]) => key === 'tag' ? !entry.tags.includes(value) : key === 'year' ? !entry.date.startsWith(value) : key === 'kind' ? !entry.views.some(view => view === value) : entry.category !== value)) return []
    const full=normalized([entry.title,entry.description,...entry.tags,entry.body].join(' '))
    if(!terms.every(term => full.includes(term))) return []
    const score=terms.reduce((sum,term) => sum+(normalized(entry.title).includes(term)?20:0)+(entry.tags.some(t => normalized(t).includes(term))?8:0)+(normalized(entry.description).includes(term)?4:0),0)
    return [{entry,score}]
  }).sort((a,b) => (newest ? 0 : b.score-a.score) || b.entry.date.localeCompare(a.entry.date))
  return ranked.map(({entry}) => ({data:async() => {
    const body=entry.body.replace(/```[^\n]*\n/g,'').replace(/[#*>`]/g,'').replace(/\s+/g,' ')
    const found=terms.map(term => normalized(body).indexOf(term)).filter(i => i>=0)
    const start=Math.max(0,(found.length?Math.min(...found):0)-55)
    return {url:entry.url,meta:{title:entry.title,date:entry.date,category:entry.category,kind:entry.views.join(',')},excerpt:markup((start?'…':'')+body.slice(start,start+230)+'…',query)}
  }}))
}
function card(data:ResultData) {
  const article=document.createElement('article');article.className='search-result'
  const meta=document.createElement('div');meta.className='result-meta'
  const kind=document.createElement('span');kind.className='result-kind';kind.textContent=(data.meta.kind||'blog').split(',').map(view => view==='docs'?'文档':'文章').join(' · ');meta.append(kind)
  for(const text of [data.meta.category,data.meta.date].filter(Boolean)){const span=document.createElement('span');span.textContent=text!;meta.append(span)}
  const heading=document.createElement('h2'),link=document.createElement('a');link.href=siteUrl(data.url);link.textContent=data.meta.title||'未命名文章';heading.append(link)
  const excerpt=document.createElement('p');safeHighlight(excerpt,data.excerpt)
  article.append(meta,heading,excerpt)
  const seen=new Set<string>()
  for(const sub of (data.sub_results||[]).filter(sub => sub.url.includes('#')).slice(0,3)) {
    if(seen.has(sub.url))continue;seen.add(sub.url)
    const a=document.createElement('a');a.className='search-subresult';a.href=siteUrl(sub.url)
    const title=document.createElement('strong');title.textContent=sub.title.replace(/\s*#$/,'')
    const text=document.createElement('p');safeHighlight(text,sub.excerpt);a.append(title,text);article.append(a)
  }
  return article
}
async function loadMore(current:number) {
  more.disabled=true
  try {
    const data=await Promise.all(matches.slice(shown,shown+10).map(result => result.data()))
    if(current!==generation)return
    data.forEach(item => results.append(card(item)));shown+=data.length
    more.hidden=shown>=matches.length
    status.textContent=matches.length?`找到 ${matches.length} 条结果，已显示 ${shown} 条`:'没有找到匹配内容。试试减少关键词，或重置筛选条件。'
  } finally {if(current===generation)more.disabled=false}
}
async function search() {
  const current=++generation,query=input.value.trim()
  const filters=Object.fromEntries(keys.filter(key=>key!=='sort'&&selectors[key].value).map(key=>[key,selectors[key].value]))
  const params=new URLSearchParams();if(query)params.set('q',query)
  Object.entries(filters).forEach(([key,value])=>params.set(key,value))
  if(selectors.sort.value==='newest')params.set('sort','newest')
  history.replaceState(null,'',location.pathname+(params.size?'?'+params.toString():''))
  results.replaceChildren();matches=[];shown=0;more.hidden=true
  const active=Boolean(query || Object.keys(filters).length);suggestions.hidden=active
  if(!active){status.textContent='输入关键词，或选择条件浏览文章。支持中文、英文和代码关键词。';return}
  status.textContent='正在查找…'
  try {
    const engine=await getEngine()
    const found=engine?await engine.search(query||null,{filters,...(selectors.sort.value==='newest'?{sort:{date:'desc'}}:{})}):{results:await fallbackSearch(query,filters,selectors.sort.value==='newest')}
    if(current!==generation)return
    matches=found.results;await loadMore(current)
  }catch {if(current===generation){fallbackPromise=undefined;status.textContent='搜索暂时不可用，请重试，或从博客与文档目录继续浏览。'}}
}
function schedule(){generation++;clearTimeout(timer);if(!composing)timer=setTimeout(search,180)}
input.addEventListener('input',schedule)
input.addEventListener('compositionstart',()=>{composing=true;clearTimeout(timer);generation++})
input.addEventListener('compositionend',()=>{composing=false;schedule()})
form.addEventListener('submit',event=>{event.preventDefault();clearTimeout(timer);void search()})
keys.forEach(key=>selectors[key].addEventListener('change',()=>{clearTimeout(timer);void search()}))
more.addEventListener('click',()=>{void loadMore(generation).catch(()=>{status.textContent='结果加载失败，请重试。'})})
document.querySelector('#search-reset')!.addEventListener('click',()=>{form.reset();clearTimeout(timer);void search();input.focus()})
document.querySelectorAll<HTMLButtonElement>('[data-search-term]').forEach(button=>button.addEventListener('click',()=>{input.value=button.dataset.searchTerm!;void search();input.focus()}))
input.addEventListener('keydown',event=>{if(event.key==='ArrowDown'){const link=results.querySelector<HTMLAnchorElement>('a');if(link){event.preventDefault();link.focus()}}})
results.addEventListener('keydown',event=>{
  if(event.key!=='ArrowDown'&&event.key!=='ArrowUp')return
  const links=[...results.querySelectorAll<HTMLAnchorElement>('a')],index=links.indexOf(document.activeElement as HTMLAnchorElement)
  if(index<0)return;event.preventDefault()
  if(event.key==='ArrowUp'&&index===0)input.focus();else links[index+(event.key==='ArrowDown'?1:-1)]?.focus()
})
function restore() {const params=new URLSearchParams(location.search);input.value=params.get('q')||'';keys.forEach(key=>{selectors[key].value=params.get(key)||(key==='sort'?'relevance':'')});void search()}
window.addEventListener('popstate',restore)
restore();input.focus()
