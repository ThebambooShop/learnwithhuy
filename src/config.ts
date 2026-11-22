/**
 * Cấu hình chung của website LearnWithHuy.
 * Cập nhật các giá trị trong file này khi có thông tin thật (social, email, domain).
 */
export const SITE = {
  name: 'LearnWithHuy',
  tagline: 'Cùng Huy học AI và công nghệ, từng bước một',
  description:
    'Kiến thức dễ hiểu, ví dụ thực tế, ứng dụng được ngay. Blog LearnWithHuy chia sẻ về AI, công nghệ và cách ứng dụng vào học tập, công việc và cuộc sống.',
  // TODO: cập nhật email thật trước khi triển khai.
  email: 'hello@learnwithhuy.vn',
  // TODO: cập nhật các liên kết mạng xã hội thật. Bỏ chuỗi rỗng → liên kết sẽ được ẩn đi ở giao diện.
  social: {
    facebook: 'https://facebook.com/learnwithhuy',
    youtube: 'https://youtube.com/@learnwithhuy',
    linkedin: 'https://linkedin.com/in/learnwithhuy',
    github: 'https://github.com/learnwithhuy',
  },
  copyright: 'LearnWithHuy',
} as const;

export const NEWSLETTER_NOTE =
  'Chúng tôi chỉ dùng email của bạn để gửi bản tin định kỳ về bài viết mới, không chia sẻ cho bên thứ ba.';
