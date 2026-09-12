<script lang="ts">
import { onMount } from "svelte";
import { getPostUrlBySlug, url } from "../utils/url-utils";
interface Post {
	slug: string;
	data: {
		title: string;
		tags: string[];
		category?: string | null;
		published: Date;
	};
}
export let sortedPosts: Post[] = [];
let tags: string[] = [];
let categories: string[] = [];
let uncategorized = false;
onMount(() => {
	const params = new URLSearchParams(window.location.search);
	tags = params.getAll("tag");
	categories = params.getAll("category");
	uncategorized = params.has("uncategorized");
});
$: filtered = sortedPosts.filter(
	(post) =>
		(!tags.length || post.data.tags.some((tag) => tags.includes(tag))) &&
		(!categories.length || categories.includes(post.data.category || "")) &&
		(!uncategorized || !post.data.category),
);
$: years = [
	...new Set(
		filtered.map((post) => new Date(post.data.published).getFullYear()),
	),
].sort((a, b) => b - a);
$: filters = [
	...categories,
	...tags.map((tag) => `# ${tag}`),
	...(uncategorized ? ["未分类"] : []),
];
function shortDate(date: Date) {
	return new Date(date).toISOString().slice(5, 10);
}
</script>
<section class="surface archive-panel">
    <div class="archive-title"><h1>文章归档<span>{filtered.length} 篇</span></h1><p>让每一次思考，都有迹可循。</p></div>
    {#if filters.length}<div class="archive-filters">{#each filters as label}<span class="tag-pill">{label}</span>{/each}<a href={url("/archive/")}>查看全部 ×</a></div>{/if}
    {#each years as year}
        <section class="archive-year"><h2>{year}<span>{filtered.filter(post => new Date(post.data.published).getFullYear() === year).length} 篇文章</span></h2>
            {#each filtered.filter(post => new Date(post.data.published).getFullYear() === year) as post}
                <a class="archive-post" href={getPostUrlBySlug(post.slug)}><time datetime={new Date(post.data.published).toISOString()}>{shortDate(post.data.published)}</time><strong>{post.data.title}</strong><span>↗</span></a>
            {/each}
        </section>
    {/each}
    {#if !filtered.length}<p class="archive-empty">暂时没有相关文章。<a href={url("/archive/")}>浏览全部文章 →</a></p>{/if}
</section>
