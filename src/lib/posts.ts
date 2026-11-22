import { getCollection, type CollectionEntry } from 'astro:content';
import { getTopic } from '../data/topics';

export type Post = CollectionEntry<'posts'>;

export const WORDS_PER_MINUTE = 200;

/** Tính thời gian đọc (phút) — tiếng Việt đọc khoảng 200 từ/phút. */
export function readingTime(text: string): number {
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  return Math.max(1, Math.round(words / WORDS_PER_MINUTE));
}

const dateFormat = new Intl.DateTimeFormat('vi-VN', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
});

export function formatDate(date: Date): string {
  return dateFormat.format(date);
}

export function compareByDateDesc(a: Post, b: Post): number {
  return b.data.date.getTime() - a.data.date.getTime();
}

export function compareByViewsDesc(a: Post, b: Post): number {
  if (b.data.views !== a.data.views) return b.data.views - a.data.views;
  return compareByDateDesc(a, b);
}

/** Bài viết đã xuất bản (loại nháp), sắp mới nhất trước. */
export async function getPublishedPosts(): Promise<Post[]> {
  const posts = await getCollection('posts', ({ data }) => !data.draft);
  return posts.sort(compareByDateDesc);
}

export function getTopicOf(post: Post) {
  return getTopic(post.data.topic);
}

/** Bỏ cú pháp Markdown để dùng cho chỉ mục tìm kiếm phía client. */
export function stripMarkdown(md: string): string {
  return md
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]*)`/g, '$1')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/^\s{0,3}#{1,6}\s+/gm, '')
    .replace(/^\s{0,3}>\s?/gm, '')
    .replace(/^\s{0,3}([-*_]\s?){3,}\s*$/gm, ' ')
    .replace(/\|/g, ' ')
    .replace(/[*_~]+/g, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}
