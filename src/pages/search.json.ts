import type { APIRoute } from "astro";
import { getSortedPosts } from "../utils/content-utils";
import { getPostUrlBySlug } from "../utils/url-utils";
export const GET: APIRoute = async () => {
	const posts = await getSortedPosts();
	const index = posts.map((post) => ({
		title: post.data.title,
		description: post.data.description,
		url: getPostUrlBySlug(post.slug),
		text: [
			post.data.title,
			post.data.description,
			post.data.category,
			...post.data.tags,
			post.body,
		]
			.join(" ")
			.toLocaleLowerCase(),
	}));
	return new Response(JSON.stringify(index), {
		headers: { "Content-Type": "application/json; charset=utf-8" },
	});
};
