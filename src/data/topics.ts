/**
 * Danh mục chủ đề của blog, tổ chức theo 4 nhóm.
 * `slug` khớp với giá trị `topic` trong frontmatter của bài viết.
 * `group` dùng để render trang /chu-de/ theo nhóm.
 */

export type TopicGroupSlug = 'hieu-ve-ai' | 'su-dung-ai' | 'xay-dung-voi-ai' | 'doi-song-va-xa-hoi';

export interface TopicGroup {
  slug: TopicGroupSlug;
  name: string;
  description: string;
}

export const topicGroups: TopicGroup[] = [
  {
    slug: 'hieu-ve-ai',
    name: 'Hiểu về AI',
    description: 'Cách AI hoạt động: từ khái niệm nền tảng đến Machine Learning và mô hình ngôn ngữ lớn.',
  },
  {
    slug: 'su-dung-ai',
    name: 'Sử dụng AI',
    description: 'Dùng AI hiệu quả hằng ngày: viết prompt, chọn công cụ, áp dụng vào công việc, dạy học và học ngoại ngữ.',
  },
  {
    slug: 'xay-dung-voi-ai',
    name: 'Xây dựng với AI',
    description: 'Xây dựng sản phẩm với AI: lập trình, kiến trúc AI Agent và hạ tầng agent harness.',
  },
  {
    slug: 'doi-song-va-xa-hoi',
    name: 'AI trong đời sống và xã hội',
    description: 'Tác động của AI đến xã hội: đọc xu hướng công nghệ một cách bình tĩnh, có bằng chứng.',
  },
];

export interface Topic {
  slug: string;
  name: string;
  description: string;
  /** Nhóm chủ đề — phải khớp slug của một nhóm trong topicGroups */
  group: TopicGroupSlug;
}

export const topics: Topic[] = [
  // Nhóm 1 — Hiểu về AI
  {
    slug: 'ai-co-ban',
    name: 'AI cơ bản',
    description:
      'Những khái niệm nền tảng về trí tuệ nhân tạo, giải thích bằng ngôn ngữ thường ngày cho người mới bắt đầu.',
    group: 'hieu-ve-ai',
  },
  {
    slug: 'machine-learning',
    name: 'Machine Learning',
    description:
      'Machine học từ dữ liệu: phân biệt Machine Learning với Generative AI, kèm các khóa nền tảng đáng học từ Andrew Ng, Google, fast.ai và Stanford.',
    group: 'hieu-ve-ai',
  },
  {
    slug: 'generative-ai-llm',
    name: 'Generative AI và LLM',
    description:
      'Mô hình ngôn ngữ lớn, AI sinh nội dung và cách chúng hoạt động — bằng những ví dụ đơn giản, dễ hình dung.',
    group: 'hieu-ve-ai',
  },
  // Nhóm 2 — Sử dụng AI
  {
    slug: 'prompt-engineering',
    name: 'Prompt Engineering',
    description:
      'Nghệ thuật đặt câu hỏi cho AI: cách viết yêu cầu rõ ràng để nhận kết quả đúng ý ngay từ lần đầu.',
    group: 'su-dung-ai',
  },
  {
    slug: 'cong-cu-ai',
    name: 'Công cụ AI',
    description:
      'Trải nghiệm các công cụ AI hữu ích cho việc học, làm việc và sáng tạo — kèm cách dùng thực tế.',
    group: 'su-dung-ai',
  },
  {
    slug: 'ai-trong-cong-viec',
    name: 'AI trong công việc',
    description:
      'Ứng dụng AI vào tác vụ hằng ngày ở văn phòng: viết, tóm tắt, lên kế hoạch và tiết kiệm thời gian.',
    group: 'su-dung-ai',
  },
  {
    slug: 'ai-trong-giao-duc',
    name: 'AI trong giáo dục',
    description:
      'Dùng AI để soạn bài, thiết kế kiểm tra đánh giá, xây dựng học liệu số và quản lý lớp học — kèm nguyên tắc dùng có trách nhiệm cho nhà giáo.',
    group: 'su-dung-ai',
  },
  {
    slug: 'tieng-anh-voi-ai',
    name: 'Tiếng Anh với AI',
    description:
      'Dùng AI làm gia sư tiếng Anh cá nhân: luyện nghe, nói, đọc, viết và xây kho từ vựng tech bằng công cụ AI — lộ trình thực dụng cho dân IT.',
    group: 'su-dung-ai',
  },
  // Nhóm 3 — Xây dựng với AI
  {
    slug: 'lap-trinh-va-cong-nghe',
    name: 'Lập trình và công nghệ',
    description:
      'Bắt đầu học lập trình, làm quen công nghệ mới và dùng AI như một trợ giảng kiên nhẫn — kèm RAG nâng cao và hệ thống retrieval thực tế.',
    group: 'xay-dung-voi-ai',
  },
  {
    slug: 'ai-agent-va-tu-dong-hoa',
    name: 'AI Agent và tự động hóa',
    description:
      'Cách agent lập kế hoạch, sử dụng công cụ và tự động hóa quy trình — phân biệt AI Agent với chatbot, từ kiến trúc nền tảng đến hệ thống chạy thực tế.',
    group: 'xay-dung-voi-ai',
  },
  {
    slug: 'harness-engineer',
    name: 'Harness Engineer',
    description:
      'Phần hạ tầng bao quanh AI Agent — đặc tả tác vụ, cung cấp ngữ cảnh, môi trường thực thi, phản hồi xác minh và quản lý trạng thái — tự tay dựng một agent harness chạy được từ con số 0.',
    group: 'xay-dung-voi-ai',
  },
  // Nhóm 4 — AI trong đời sống và xã hội
  {
    slug: 'goc-nhin-va-xu-huong',
    name: 'Góc nhìn và xu hướng công nghệ',
    description:
      'Đọc tin công nghệ một cách bình tĩnh, có chọn lọc — đánh giá xu hướng bằng bằng chứng thay vì theo hâm mộ.',
    group: 'doi-song-va-xa-hoi',
  },
];

export function getTopic(slug: string): Topic | undefined {
  return topics.find((t) => t.slug === slug);
}
