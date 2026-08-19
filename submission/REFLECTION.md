# Reflection — Lab 19

**Tên:** Đỗ Ngọc Bích
**Cohort:** A20 - K3
**Path đã chạy:** Docker + lite smoke test

---

## Câu hỏi (≤ 200 chữ)

> Trên golden set 50 queries, mode nào thắng ở loại query nào (`exact` /
> `paraphrase` / `mixed`), và tại sao? Khi nào bạn **không** dùng hybrid
> (i.e. khi nào pure BM25 hoặc pure vector là lựa chọn đúng)?

Trên golden set 50 queries, BM25 phù hợp nhất với nhóm `exact` vì các thuật
ngữ kỹ thuật xuất hiện nguyên văn trong corpus. Semantic search phù hợp hơn
với ý định paraphrase, nhưng với corpus tiếng Việt và model `bge-small-en`
thì kết quả thực tế chưa vượt BM25. Hybrid RRF đạt kết quả trung bình cao
nhất (78.6%), đồng thời thắng rõ ở nhóm `mixed` (100.0%) vì kết hợp được tín
hiệu từ khóa và ngữ nghĩa. Tôi không dùng hybrid khi query chứa thuật ngữ
chính xác, corpus có tên mã hoặc ID cần khớp tuyệt đối, và BM25 đã đủ nhanh.

Tôi cũng không chọn pure vector cho các truy vấn cần lọc metadata nghiêm ngặt
hoặc khi embedding model không phù hợp ngôn ngữ. Trong production, tôi sẽ
đo lại với embedding multilingual trước khi quyết định ngưỡng và chiến lược
cuối cùng.

---

## Điều ngạc nhiên nhất khi làm lab này

Hybrid không tự động tốt hơn trong mọi slice: chất lượng phụ thuộc embedding
model, tokenizer và cách thiết kế golden set. NB7 cũng cho thấy cache có thể
tiết kiệm chi phí nhưng gây false hit hoặc rò chéo tenant nếu thiếu namespace.

---

## Bonus challenge

- [X] Đã làm bonus (xem `bonus/`)
- [ ] Pair work với: Không có
