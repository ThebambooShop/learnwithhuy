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
