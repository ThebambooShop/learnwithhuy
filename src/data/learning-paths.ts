/**
 * Lộ trình học (elearning) — gom các bài viết thành chuỗi học có thứ tự
 * theo chủ đề. `lessons` là danh sách slug bài viết (khớp `id` của post),
 * xếp theo thứ tự học gợi ý.
 */
import type { Post } from '../lib/posts';
import { getPublishedPosts, readingTime } from '../lib/posts';

export type PathLevel = 'Mới bắt đầu' | 'Trung cấp' | 'Nâng cao';

export interface LearningPath {
  slug: string;
  title: string;
  description: string;
  /** Phải khớp một chủ đề trong src/data/topics.ts */
  topic: string;
  level: PathLevel;
  /** Học xong lộ trình, bạn sẽ làm được gì */
  outcomes: string[];
  /** Kiến thức nên có trước khi bắt đầu */
  prerequisites?: string[];
  /** Slug các bài viết theo thứ tự học */
  lessons: string[];
}

export const learningPaths: LearningPath[] = [
  {
    slug: 'claude-trong-doanh-nghiep',
    title: 'Claude cho doanh nghiệp: từ cá nhân giỏi đến hệ thống vận hành',
    description:
      'Lộ trình 8 bài xây hệ thống AI Agent với Claude: tư duy đúng, kiến trúc 7 tầng, CLAUDE.md và Skills, kết nối hệ thống, cấu trúc prompt 6 lớp, lộ trình 30 ngày cho 8 phòng ban, content marketing và cỗ máy content tự động.',
    topic: 'cong-cu-ai',
    level: 'Mới bắt đầu',
    outcomes: [
      'Hiểu vì sao "vài cá nhân giỏi dùng AI" chưa đủ và cần hệ thống 7 tầng',
      'Viết được CLAUDE.md chuẩn 6 phần và Skill 6 thành phần cho công việc lặp lại',
      'Kết nối Claude với dữ liệu thật qua Connectors, MCP và sub-agents một cách an toàn',
      'Giao việc cho Claude bằng cấu trúc prompt 6 lớp với checklist kiểm tra',
      'Lập được lộ trình triển khai 30 ngày cho các phòng ban trong tổ chức',
    ],
    lessons: [
      'claude-doanh-nghiep-tu-duy-va-he-sinh-thai',
      'claude-kienc-truc-7-tang-6-tai-san-tri-thuc',
      'claude-claude-md-project-skills',
      'claude-connectors-mcp-sub-agents',
      'prompt-giao-viec-6-lop-best-practices',
      'claude-8-phong-ban-lo-trinh-30-ngay',
      'claude-content-marketing-9-prompt',
      'co-may-content-claude-4-agent',
    ],
  },
  {
    slug: 'ai-agent-engineer',
    title: 'Trở thành AI Agent Engineer trong 17 tuần',
    description:
      'Lộ trình 3 bài cho kỹ sư muốn xây dựng, đánh giá và triển khai hệ thống AI Agent production: guide nền tảng của OpenAI, kho 47 tài nguyên học tập và roadmap Harness Engineering 6 giai đoạn 17 tuần.',
    topic: 'lap-trinh-va-cong-nghe',
    level: 'Nâng cao',
    prerequisites: [
      'Nền tảng kỹ thuật: Python, cơ bản về API và Git',
      'Hiểu cách LLM hoạt động ở mức khái niệm',
    ],
    outcomes: [
      'Phân biệt workflow và agent, nắm 4 nguyên tắc Context Engineering',
      'Biết kho 47 tài nguyên học AI Agent xếp theo thứ tự: video, GitHub, whitepaper, sách, papers, khóa học',
      'Có lộ trình 17 tuần rõ mốc: agent loop 100 dòng → LangGraph deep agent → mini-harness 1.500 dòng → evals + CI gates',
      'Hiểu vì sao Harness quan trọng hơn Model và tránh các bẫy multi-agent thổi phồng',
    ],
    lessons: [
      'huong-dan-xay-dung-agent-thuc-te',
      'lo-trinh-hoc-ai-agent-a-z',
      'ai-engineer-roadmap-2026',
    ],
  },
  {
    slug: 'ai-agent-tu-chu-9router-hermes',
    title: 'AI Agent tự chủ với 9Router và Hermes Agent',
    description:
      'Lộ trình 3 bài đi từ nền tảng agent thực tế đến hai công cụ mã nguồn mở: cổng định tuyến 9Router và Hermes Agent — hiểu vai trò, cài đặt từ con số 0 trên cả ba hệ điều hành.',
    topic: 'cong-cu-ai',
    level: 'Trung cấp',
    prerequisites: [
      'Làm quen cơ bản với terminal (cd, curl, chạy lệnh)',
      'Hiểu khái niệm API và API key',
    ],
    outcomes: [
      'Phân biệt vai trò tầng định tuyến mô hình và tầng tác vụ tự chủ trong kiến trúc AI',
      'Hiểu cơ chế RTK Token Saver, 3-Tier Fallback và định tuyến combo của 9Router',
      'Cài đặt Hermes Agent bản CLI và Desktop trên Windows, macOS, Linux',
      'Kết nối Hermes Agent vào 9Router và chọn combo định tuyến',
      'Nắm 6 khái niệm cốt lõi: CLI, Session, Tools, Skills, Memory, MCP',
    ],
    lessons: [
      'huong-dan-xay-dung-agent-thuc-te',
      '9router-va-hermes-agent',
      'cai-dat-hermes-agent-tu-so-0',
    ],
  },
  {
    slug: 'rag-nang-cao',
    title: 'RAG nâng cao: từ Hybrid Search đến đánh giá hệ thống',
    description:
      'Lộ trình 5 bài thực hành Python: hybrid search BM25 + RRF, GraphRAG với knowledge graph, multi-hop RAG trên LangGraph, RAG đa phương thức cho PDF, và đánh giá chất lượng bằng Ragas.',
    topic: 'lap-trinh-va-cong-nghe',
    level: 'Nâng cao',
    prerequisites: [
      'Nắm được cách LLM hoạt động ở mức khái niệm',
      'Python cơ bản: hàm, import, cài thư viện bằng pip',
    ],
    outcomes: [
      'Xây được pipeline hybrid search kết hợp BM25, dense retrieval và RRF',
      'Xây dựng knowledge graph bằng Microsoft GraphRAG và dùng Local/Global Search',
      'Thiết kế multi-hop RAG lặp trên LangGraph với khử đại từ và phát hiện mâu thuẫn',
      'Xử lý tài liệu PDF chứa bảng biểu và biểu đồ bằng pipeline đa phương thức',
      'Đánh giá chất lượng RAG định lượng bằng Ragas với Golden Dataset',
    ],
    lessons: [
      'hybrid-search-bm25-dense-rrf',
      'graphrag-knowledge-graph',
      'multi-hop-rag-langgraph',
      'multimodal-rag-pdf-tieng-viet',
      'danh-gia-chat-luong-rag-ragas',
    ],
  },
  {
    slug: 'ai-agent-architecture',
    title: 'Kiến trúc AI Agent: từ agent loop đến production',
    description:
      'Lộ trình 8 bài tổng hợp kiến thức thực hành từ 3 kho học liệu lớn — AI Agents for Beginners của Microsoft, GenAI Agents (64 notebook) và All Agentic Architectures (36 kiến trúc chạy được) cùng 12 nguyên lý production của HumanLayer. Từ agent loop đầu tiên đến bản đồ chọn architecture cho bài toán thật, đóng trên một dự án xuyên suốt: trợ lý tra cứu tài liệu nội bộ. Thời gian đọc toàn bộ khoảng 95 phút; làm đầy đủ bài tập thực hành cần thêm 4-6 giờ. Bài 1-4 là kiến trúc cốt lõi; bài 5-8 là phần mở rộng thiết kế và vận hành — một agent đơn giản (bài 1-2) đã đủ cho phần lớn tác vụ cơ bản.',
    topic: 'lap-trinh-va-cong-nghe',
    level: 'Trung cấp',
    prerequisites: [
      'Python cơ bản: đã viết được script dùng hàm, dict, vòng lặp và xử lý lỗi (try/except)',
      'Quen terminal: cài thư viện bằng pip, chạy file Python, dùng biến môi trường (export)',
      'Hiểu API key và chi phí gọi API ở mức cơ bản — mỗi lượt gọi model đều tốn tiền',
    ],
    outcomes: [
      'Xây dựng được agent loop hoàn chỉnh ~100 dòng Python không framework và biết khi nào KHÔNG nên dùng agent',
      'Áp dụng đúng từng pattern: routing, tool design, planning, reflection, memory, multi-agent, RAG trong agent',
      'Thiết kế memory và context engineering theo mô hình phân tầng MemGPT để agent vận hành ổn định và tiết kiệm token',
      'Kiểm tra được 12 nguyên lý production với agent của mình: human-in-the-loop, stateless reducer, evals, guardrails',
      'Chọn được architecture phù hợp từ bản đồ 36 kiến trúc cho bài toán thật của bạn',
    ],
    lessons: [
      'nen-tang-agent-va-agent-loop',
      'agent-routing-va-tool-design',
      'agent-planning-va-reflection',
      'agent-memory-va-context-engineering',
      'agent-multi-agent-orchestration',
      'agent-rag-va-graphrag',
      '12-nguyen-ly-agent-production',
      'chon-agent-architecture-36-mau',
    ],
  },
];

export function getPath(slug: string): LearningPath | undefined {
  return learningPaths.find((p) => p.slug === slug);
}

/** Bài viết của một lộ trình, giữ đúng thứ tự học trong `lessons`. */
export async function getPathPosts(path: LearningPath): Promise<Post[]> {
  const all = await getPublishedPosts();
  const byId = new Map(all.map((p) => [p.id, p]));
  return path.lessons.map((slug) => byId.get(slug)).filter((p) => p !== undefined);
}

/** Tổng thời gian đọc của một lộ trình (phút). */
export function pathReadingMinutes(path: LearningPath, posts: Post[]): number {
  return posts.reduce((sum, p) => sum + readingTime(p.body ?? ''), 0);
}

/** Tìm lộ trình chứa một bài viết (kèm vị trí trong lộ trình). */
export function findPathOfPost(
  slug: string,
): { path: LearningPath; position: number } | undefined {
  for (const path of learningPaths) {
    const position = path.lessons.indexOf(slug);
    if (position !== -1) return { path, position };
  }
  return undefined;
}
