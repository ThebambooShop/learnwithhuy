/**
 * Danh mục chủ đề của blog.
 * `slug` khớp với giá trị `topic` trong frontmatter của bài viết.
 */
export interface Topic {
  slug: string;
  name: string;
  description: string;
}

export const topics: Topic[] = [
  {
    slug: 'ai-co-ban',
    name: 'AI cơ bản',
    description:
      'Những khái niệm nền tảng về trí tuệ nhân tạo, giải thích bằng ngôn ngữ thường ngày cho người mới bắt đầu.',
  },
  {
    slug: 'generative-ai-llm',
    name: 'Generative AI và LLM',
    description:
      'Mô hình ngôn ngữ lớn, AI sinh nội dung và cách chúng hoạt động — bằng những ví dụ đơn giản, dễ hình dung.',
  },
  {
    slug: 'prompt-engineering',
    name: 'Prompt Engineering',
    description:
      'Nghệ thuật đặt câu hỏi cho AI: cách viết yêu cầu rõ ràng để nhận kết quả đúng ý ngay từ lần đầu.',
  },
  {
    slug: 'cong-cu-ai',
    name: 'Công cụ AI',
    description:
      'Trải nghiệm các công cụ AI hữu ích cho việc học, làm việc và sáng tạo — kèm cách dùng thực tế.',
  },
  {
    slug: 'machine-learning',
    name: 'Machine Learning',
    description:
      'Machine học từ dữ liệu: phân biệt Machine Learning với Generative AI và biết khi nào dùng cái nào.',
  },
  {
    slug: 'lap-trinh-va-cong-nghe',
    name: 'Lập trình và công nghệ',
    description:
      'Bắt đầu học lập trình, làm quen công nghệ mới và dùng AI như một trợ giảng kiên nhẫn.',
  },
  {
    slug: 'ai-trong-cong-viec',
    name: 'AI trong công việc',
    description:
      'Ứng dụng AI vào tác vụ hằng ngày ở văn phòng: viết, tóm tắt, lên kế hoạch và tiết kiệm thời gian.',
  },
  {
    slug: 'goc-nhin-va-xu-huong',
    name: 'Góc nhìn và xu hướng công nghệ',
    description:
      'Đọc tin công nghệ một cách bình tĩnh, có chọn lọc — đánh giá xu hướng bằng bằng chứng thay vì theo hâm mộ.',
  },
  // Harness Engineer — chương trình chuyên sâu về harness engineering: vì sao agent mạnh vẫn thất bại, 5 lớp phòng thủ, 14 bài giảng + chuỗi Mini-dsh tự tay dựng harness
  {
    slug: 'harness-engineer',
    name: 'Harness Engineer',
    description:
      'Chương trình Harness Engineer: vì sao agent mạnh vẫn thất bại, năm lớp phòng thủ của harness (đặc tả, ngữ cảnh, môi trường, xác minh, trạng thái) và tự tay dựng một agent harness hoàn chỉnh từ con số 0.',
  },
  // AI ứng dụng theo ngành — cách AI thay đổi công việc thực tế của từng nghề, gói trong chính ví dụ của nghề đó
  {
    slug: 'ai-trong-giao-duc',
    name: 'AI trong giáo dục',
    description:
      'Dùng AI để soạn bài, thiết kế kiểm tra đánh giá, xây dựng học liệu số và quản lý lớp học — kèm nguyên tắc dùng có trách nhiệm cho nhà giáo.',
  },
  {
    slug: 'ai-trong-y-te',
    name: 'AI trong y tế',
    description:
      'Cách AI hỗ trợ chẩn đoán, chuyển đổi hồ sơ bệnh án và chăm sóc người bệnh — cùng ranh giới an toàn khi làm việc với dữ liệu sức khỏe.',
  },
  {
    slug: 'ai-trong-san-xuat',
    name: 'AI trong sản xuất',
    description:
      'Bảo trì dự đoán, kiểm tra chất lượng, tối ưu dây chuyền — các ứng dụng AI đã chạy thực tế trong nhà máy, không phải trên giấy.',
  },
  {
    slug: 'ai-trong-tai-chinh',
    name: 'AI trong tài chính - ngân hàng',
    description:
      'AI cho chấm điểm tín dụng, phát hiện gian lận và chăm sóc khách hàng — kèm những yêu cầu tuân thủ đặc thù của ngành tài chính.',
  },
  {
    slug: 'ai-trong-ban-le',
    name: 'AI trong bán lẻ',
    description:
      'Dự báo nhu cầu, cá nhân hóa trải nghiệm mua sắm và tối ưu tồn kho — AI hỗ trợ ra quyết định kinh doanh như thế nào trong chuỗi bán lẻ.',
  },
  {
    slug: 'ai-trong-logistics',
    name: 'AI trong logistics',
    description:
      'Tối ưu tuyến vận chuyển, dự báo tồn kho, tự động hóa kho bãi — ứng dụng AI trong chuỗi cung ứng từ kho đến tay người nhận.',
  },
  {
    slug: 'ai-trong-hanh-chinh-cong',
    name: 'AI trong hành chính công',
    description:
      'AI hỗ trợ soạn thảo văn bản, phân tích dữ liệu và phục vụ người dân — nền tảng thực dụng cho chuyển đổi số ở cơ quan nhà nước.',
  },
  // Tiếng Anh với AI — dùng AI làm gia sư, luyện nghe nói đọc viết cho dân IT
  {
    slug: 'tieng-anh-voi-ai',
    name: 'Tiếng Anh với AI',
    description:
      'Dùng AI làm gia sư tiếng Anh cá nhân: luyện nghe, nói, đọc, viết và xây kho từ vựng tech bằng công cụ AI — lộ trình thực dụng cho dân IT.',
  },
];

export function getTopic(slug: string): Topic | undefined {
  return topics.find((t) => t.slug === slug);
}
