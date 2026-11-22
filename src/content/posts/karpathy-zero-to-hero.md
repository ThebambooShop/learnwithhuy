---
title: "Karpathy Zero to Hero: học LLM bằng cách code cùng video — micrograd, makemore, GPT, tokenizer"
description: "Bài học elearning phân tích series Neural Networks: Zero to Hero của Andrej Karpathy — lộ trình video từ backpropagation viết tay đến GPT và tokenizer, kèm ý nghĩa từng phần và cách học theo code."
topic: "generative-ai-llm"
date: "2026-11-19"
cover: "/images/covers/posts/karpathy-zero-to-hero.jpg"
views: 190
faq:
  - q: "Series Karpathy phù hợp trình độ nào?"
    a: "Cần Python cơ bản và nhẹ nhàng về đại số tuyến tính. Karpathy giải thích từng dòng code trên màn hình nên người mới ngành có theo được — nhưng để thật sự thu được kỹ năng thì phải tự gõ và tự dừng video làm theo, không xem thụ động."
  - q: "Xem video hay học sách (LLMs-from-scratch) trước?"
    a: "Hai tài nguyên bổ trợ nhau: video Karpathy trực quan và có nhịp giải thích chậm hơn, phù hợp để hiểu khái niệm lần đầu; sách LLMs-from-scratch hệ thống và có exercise đầy đủ hơn. Phổ biến nhất là xem video trước rồi luyện sâu bằng repo."
  - q: "Tại sao series này được coi là kinh điển?"
    a: "Karpathy từng là founding member của OpenAI và trước đó là Tesla AI director — cách anh dạy đặc biệt ở chỗ viết từng dòng code từ số không, không dùng thư viện che khái niệm. Series được nhắc tới nhiều nhất trong các danh sách biên tập tài nguyên LLM."
---

Nếu chỉ chọn được **một** nguồn video để hiểu LLM vận hành bên trong, cộng đồng nhiều năm qua vẫn trả lời một tên: [Neural Networks: Zero to Hero](https://karpathy.ai/zero-to-hero.html) của Andrej Karpathy — ex-director of AI tại Tesla, founding member OpenAI. Series được Awesome-LLM liệt kê đầu bảng nhóm tutorial video với nhận định về chất lượng giảng dạy hiếm có.

Điểm khác biệt so với khóa học đại trà: mọi khái niệm đều được **viết thành code từ con số không** trên màn hình, không thư viện "magic" nào che khái niệm. Bạn sẽ thấy backpropagation thực chất chỉ là đạo hàm chuỗi, và GPT là một vòng lặp attention + feed-forward lặp lại N lần.

<div style="margin:1.6em 0;">
  <span class="level-badge level-badge--mid">🟡 Trung cấp</span>
  <span class="level-badge">🎬 Video series</span>
  <span class="level-badge">⏱️ 4–6 tuần</span>
</div>

## Lộ trình các video theo thứ tự

<ol class="steps">
  <li>
    <p class="st-title">1. The spelled-out intro to neural networks & backpropagation</p>
    <p class="st-desc">Viết micrograd: một autograd engine nhỏ — hiểu chính xác gradient chảy qua network như thế nào bằng cách tự đạo hàm từng phép tính.</p>
  </li>
  <li>
    <p class="st-title">2. Makemore series (4 video)</p>
    <p class="st-desc">Bigram, MLP, BatchNorm, WaveNet — mỗi video thêm một tầng kiến trúc vào cùng một bài toán sinh tên. Bạn thấy rõ vì sao mỗi cải tiến ra đời và nó sửa lỗi gì của phần trước.</p>
  </li>
  <li>
    <p class="st-title">3. Let's build GPT from scratch</p>
    <p class="st-desc">Video nổi tiếng nhất: attention mechanism viết tay trong ~100 dòng, ghép thành GPT nhỏ train trên Shakespeare, sinh văn bản theo phong cách.</p>
  </li>
  <li>
    <p class="st-title">4. Let's build the GPT Tokenizer</p>
    <p class="st-desc">Byte pair encoding từ đầu — hiểu vì sao token hóa là phần "khó chịu" nhất của mọi LLM: lỗi tiếng Việt, phép tính, code đều bắt nguồn từ đây.</p>
  </li>
  <li>
    <p class="st-title">5. Let's reproduce GPT-2 (124M)</p>
    <p class="st-desc">Scale lên thật: mixed precision, gradient accumulation, distributed training — bước chuyển từ "hiểu cơ chế" sang "biết train model ở scale thực tế".</p>
  </li>
</ol>

## Khái niệm cốt lõi được dạy hay nhất

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">↩️</span>
    <h3 class="cc-name">Backpropagation chỉ là đạo hàm chuỗi có tổ chức</h3>
  </div>
  <div class="cc-body">
    <p>Mỗi phép tính trong network là một node trong graph; backprop đi ngược graph và nhân các đạo hàm cục bộ lại (chain rule). Khi tự viết micrograd, bạn ngừng coi backprop là "thư viện làm hộ" và hiểu vì sao gradient đúng — nền tảng để debug mọi bài toán training sau này.</p>
  </div>
</div>

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">👀</span>
    <h3 class="cc-name">Attention là "hợp đồng thông tin" giữa token</h3>
  </div>
  <div class="cc-body">
    <p>Karpathy gọi attention là cơ chế giao tiếp có định hướng: mỗi token phát ra query — những gì nó đang tìm, key — những gì nó có thể cung cấp, và value — nội dung thật nếu được chọn. Trọng số softmax quyết định mức trộn thông tin từ token khác. Causal mask biến cơ chế này thành model sinh văn bản.</p>
  </div>
</div>

<div class="concept-card">
  <div class="cc-head">
    <span class="cc-icon">🧮</span>
    <h3 class="cc-name">Tokenizer là nguồn của nhiều bug "không thể giải thích"</h3>
  </div>
  <div class="cc-body">
    <p>Model không thấy chữ cái — nó thấy token. Vì sao LLM đếm chữ trong từ hay sai? Vì một từ có thể là một token duy nhất. Vì sao làm toán số lớn hay lỗi? Vì chữ số bị cắt vụn thành token. Hiểu tokenizer là hiểu ranh giới năng lực của model.</p>
  </div>
</div>

## Checklist thực hành

<ul class="checklist">
  <li>Xem video micrograd — dừng video gõ code theo, không copy paste</li>
  <li>Tự triển khai lại makemore MLP phần 2 mà không nhìn solution</li>
  <li>Viết attention block từ đầu trên giấy trước (shape từng bước), rồi code</li>
  <li>Train GPT Shakespeare nhỏ trên Colab — thử thay đổi learning rate và số layer, ghi nhận khác biệt</li>
  <li>Dùng tokenizer tự viết để đếm token một đoạn tiếng Việt, so với tokenizer của model thương mại</li>
</ul>

<div class="quiz">
  <p class="quiz-label">Kiểm tra nhanh</p>
  <details>
    <summary>Vì sao Makemore đi qua bigram → MLP → WaveNet thay vì nhảy thẳng transformer?</summary>
    <p class="q-answer"><strong>Đáp án:</strong> Để mỗi kiến trúc mới đều có "lý do tồn tại" rõ ràng: bigram quá ngắn hạn, MLP mở rộng context nhưng cần kỹ thuật, BatchNorm fix vấn đề phân phối activation, WaveNet xếp tầng dilation. Học theo tiến trình lịch sử giúp hiểu vì sao transformer thắng thế.</p>
  </details>
  <details>
    <summary>Điểm khác biệt chính của transformer so với RNN trong việc xử lý chuỗi?</summary>
    <p class="q-answer"><strong>Đáp án:</strong> Transformer bỏ cơ chế quay vòng tuần tự — mọi token được xử lý song song trong một forward pass, attention trực tiếp kết nối bất kỳ cặp token nào. RNN phải truyền thông tin qua từng bước, làm thông tin xa pha loãng và không parallel được.</p>
  </details>
</div>

<div class="callout callout--tip">
  <span class="co-icon">💡</span>
  <div class="co-body">
    <span class="co-title">Quy tắc xem series này</span>
    <p>Mỗi giờ video tương đương 3–4 giờ làm theo. Nếu chỉ xem không gõ code, bạn có cảm giác hiểu nhưng viết lại thì không ra — đó là ảo giác hiểu (illusion of competence).</p>
  </div>
</div>

Bổ trợ lý thuyết bằng [Xây dựng LLM từ scratch](/bai-viet/xay-dung-llm-tu-scratch/); nền khái niệm chung tại [LLM hoạt động như thế nào?](/bai-viet/llm-hoat-dong-nhu-the-nao/).

<div class="src-grid">
  <a class="src-card" href="https://karpathy.ai/zero-to-hero.html">
    <span class="sc-tag">Trang series</span>
    <p class="sc-name">karpathy.ai/zero-to-hero</p>
    <p class="sc-desc">Danh sách video chính thức + GitHub repo code từng video.</p>
  </a>
  <a class="src-card" href="https://github.com/karpathy/micrograd">
    <span class="sc-tag">Code mẫu</span>
    <p class="sc-name">karpathy/micrograd</p>
    <p class="sc-desc">Autograd engine ~100 dòng — điểm bắt đầu của cả series.</p>
  </a>
</div>
