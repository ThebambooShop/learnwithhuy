import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// TODO: đổi `site` thành domain thật khi deploy — dùng cho canonical URL, sitemap và Open Graph.
export default defineConfig({
  site: 'https://learnwithhuy.vercel.app',
  integrations: [sitemap()],
  markdown: {
    // Render công thức toán trong bài viết (RRF, MAP, Faithfulness trong chuỗi RAG)
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeKatex],
  },
});
