import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/**
 * Bộ sưu tập bài viết — dữ liệu có cấu trúc qua frontmatter.
 * Sau này muốn nối CMS, chỉ cần thay loader `glob` bằng loader/API tương ứng.
 */
const posts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/posts' }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    /** Phải khớp `slug` của một chủ đề trong src/data/topics.ts */
    topic: z.string(),
    date: z.coerce.date(),
    /** Đường dẫn ảnh bìa trong thư mục /public */
    cover: z.string(),
    featured: z.boolean().default(false),
    /** Chỉ dùng để sắp xếp "Phổ biến" trong dữ liệu mẫu — thay bằng số liệu thật (analytics) khi có. */
    views: z.number().default(0),
    draft: z.boolean().default(false),
    /** Hỏi–đáp cuối bài — render ra giao diện + FAQPage JSON-LD cho SEO */
    faq: z.array(z.object({ q: z.string(), a: z.string() })).optional(),
  }),
});

export const collections = { posts };
