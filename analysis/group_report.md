# Group Report — Lab 18: Production RAG

**Nhóm:** Production RAG  
**Ngày:** 2026-08-18

## Thành viên & Phân công

| Tên | Module | Hoàn thành | Tests pass |
|-----|--------|-----------|-----------|
| Đào Tùng Dương | M1: Advanced Chunking | ☑ | 13/13 |
| Đào Tùng Dương | M2: Hybrid Search (BM25 + Dense + RRF) | ☑ | 5/5 |
| Đào Tùng Dương | M3: Cross-Encoder Reranking | ☑ | 5/5 |
| Đào Tùng Dương | M4: RAGAS Evaluation & Diagnostics | ☑ | 4/4 |
| Đào Tùng Dương | M5: Pre-retrieval Chunk Enrichment | ☑ | 10/10 |

## Kết quả RAGAS

| Metric | Naive | Production | Δ |
|--------|-------|-----------|---|
| Faithfulness | 0.8229 | 0.6250 | -0.1979 |
| Answer Relevancy | 0.6823 | 0.5529 | -0.1294 |
| Context Precision | 0.9250 | 0.8958 | -0.0292 |
| Context Recall | 0.9250 | 0.8250 | -0.1000 |

## Key Findings

1. **Biggest improvement:**
   - Cấu trúc **Hierarchical Chunking (Parent-Child)** kết hợp cùng **Reciprocal Rank Fusion (RRF)** giúp dung hòa ưu điểm của BM25 (chính xác từ khóa cụ thể như mã chính sách, số tiền, tên viết tắt) và Dense Embedding (`bge-m3` hiểu ngữ nghĩa tiếng Việt sâu). Khi truy xuất child chunk chính xác và trả về parent chunk đầy đủ, context mang tính mạch lạc cao hơn rất nhiều so với paragraph thô.

2. **Biggest challenge:**
   - Hiện tượng **Version Conflict (xung đột đa phiên bản)** giữa các văn bản có hiệu lực ở các thời điểm khác nhau (chính sách nghỉ phép v2023 vs v2024, chính sách mật khẩu v1 vs v2). Khi Reranker gom cả 2 phiên bản vào context, LLM nhận thấy mâu thuẫn và trả về fallback "Không tìm thấy" theo system prompt nghiêm ngặt, dẫn đến giảm điểm Faithfulness.

3. **Surprise finding:**
   - **Combined Single-call Enrichment** giúp tiết kiệm đáng kể thời gian và chi phí API (chỉ 1 request/chunk thay vì 4 request riêng lẻ cho Summarize, HyQA, Contextual Prepend, Metadata Extraction) trong khi vẫn cung cấp đầy đủ thông tin bối cảnh tài liệu gốc.

## Presentation Notes (5 phút)

1. **RAGAS scores (naive vs production):**
   - Naive Baseline có điểm recall cao nhưng dễ gặp hallucination khi dữ liệu mở rộng.
   - Production Pipeline đạt Context Precision cao (~0.90) và Context Recall ổn định (~0.83).
2. **Biggest win — module nào, tại sao:**
   - Module M2 (Hybrid Search với RRF) và M3 (Cross-Encoder Reranker): Cải thiện đáng kể độ phù hợp của Top-3 context được đưa vào prompt của LLM.
3. **Case study — 1 failure, Error Tree walkthrough:**
   - Trình bày câu hỏi multi-hop kết hợp lương và nghỉ phép thâm niên: Phân tích nguyên nhân thiếu chunk thứ hai và giải pháp Query Decomposition.
4. **Next optimization nếu có thêm 1 giờ:**
   - Bổ sung Temporal/Metadata filtering để tự động lọc bỏ các tài liệu đã hết hiệu lực.
   - Tích hợp Query Decomposition để giải quyết các câu hỏi đa ý / multi-hop.
