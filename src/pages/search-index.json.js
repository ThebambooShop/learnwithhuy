import { getPublishedPosts, stripMarkdown } from '../lib/posts';

/** Chỉ mục tìm kiếm phía client — được nạp bởi SearchModal và trang /bai-viet/. */
export async function GET() {
  const posts = await getPublishedPosts();
  const data = posts.map((p) => ({
    slug: p.id,
    title: p.data.title,
    description: p.data.description,
    topic: p.data.topic,
    cover: p.data.cover,
    date: p.data.date.toISOString(),
    views: p.data.views,
    body: stripMarkdown(p.body ?? ''),
  }));
  return new Response(JSON.stringify(data), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
}
