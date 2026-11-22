# LearnWithHuy 🌱

Blog cá nhân chia sẻ kiến thức **AI, công nghệ và ứng dụng thực tế** — viết cho người mới
bắt đầu: "Kiến thức dễ hiểu, ví dụ thực tế, ứng dụng được ngay."

Xây bằng **Astro** (static site generator): nhanh, SEO tốt, nội dung là dữ liệu có cấu trúc
(content collections) — sẵn sàng nối CMS sau này.

## Chạy dự án

```bash
npm install        # cài dependencies (lần đầu)
npm run dev        # dev server tại http://localhost:4321
npm run build      # build ra thư mục dist/
npm run preview    # xem bản build tại http://localhost:4321
```

## Cấu trúc

```
src/
  config.ts              # tên site, mô tả, social, email — CẬP NHẬT THÔNG TIN THẬT Ở ĐÂY
  data/topics.ts         # danh mục 8 chủ đề (slug, tên, mô tả)
  content.config.ts      # schema frontmatter của bài viết (zod)
  content/posts/*.md     # bài viết (Markdown + frontmatter)
  lib/posts.ts           # util: thời gian đọc, định dạng ngày, bộ lọc, strip markdown
  layouts/BaseLayout.astro   # <head> SEO/OG, theme sáng–tối, Header/Footer/SearchModal
  components/            # Header, Footer, PostCard, NewsletterForm, SearchModal, ShareSave
  pages/
    index.astro          # Trang chủ
    bai-viet/index.astro # Danh sách bài viết (tìm kiếm, lọc chủ đề, sắp xếp — sync URL ?q=&chu-de=&sap-xep=)
    bai-viet/[slug].astro# Chi tiết bài viết (TOC, progress bar, chia sẻ, lưu, prev/next, liên quan)
    chu-de/index.astro   # Trang chủ đề
    chu-de/[slug].astro  # Trang một chủ đề
    ve-huy.astro         # Trang giới thiệu
    404.astro            # Trang không tìm thấy
    rss.xml.js           # Feed RSS
    search-index.json.js # Chỉ mục tìm kiếm cho phía client
public/
  images/covers/*.svg    # Ảnh bìa (SVG trừu tượng, nhất quán theo chủ đề)
  favicon.svg, robots.txt
```

## Thêm bài viết mới

Tạo file `src/content/posts/<slug>.md` (slug tiếng Việt không dấu, dùng gạch ngang —
trở thành URL `/bai-viet/<slug>/`):

```yaml
---
title: "Tiêu đề bài viết"
description: "Mô tả ngắn 1–2 câu hiển thị ở thẻ bài viết và meta description."
topic: "ai-co-ban"          # phải khớp slug chủ đề trong src/data/topics.ts
date: "2026-12-01"
cover: "/images/covers/ai-co-ban.svg"
featured: false             # true → hiện ở mục "Bài viết nổi bật" trang chủ
views: 0                    # chỉ dùng sắp xếp "Phổ biến" trong dữ liệu mẫu
draft: false                # true → không xuất bản
---
```

## Cần cấu hình thêm trước khi lên thật

1. **Domain thật**: đổi `site` trong `astro.config.mjs` và đường dẫn sitemap trong
   `public/robots.txt` (hiện là placeholder `learnwithhuy.vercel.app`).
2. **Bản tin**: mở `src/components/NewsletterForm.astro`, gán
   `NEWSLETTER_ENDPOINT` (Mailchimp/Buttondown/API riêng...) — khi chưa cấu hình,
   form chạy chế độ demo và ghi rõ điều đó cho người dùng.
3. **Thông tin cá nhân**: `src/config.ts` — email, liên kết Facebook/YouTube/LinkedIn/GitHub
   (để rỗng thì liên kết tự ẩn), ảnh đại diện `public/images/avatar.svg`.
4. **Ảnh OG**: các mạng xã hội không render SVG cho og:image — khi lên thật, xuất
   `dist/images/covers/*.svg` thành PNG (cùng tên) và thay đường dẫn trong frontmatter.
5. **Độ phổ biến**: thay trường `views` (dữ liệu mẫu) bằng số liệu thật khi có analytics.
