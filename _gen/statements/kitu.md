## Đề bài

Để làm quen với bài tập lập trình về kí tự, thầy giáo giao cho các bạn bài tập sau: Cho một dãy kí tự là các chữ cái Latinh **in hoa**. Hãy in ra các kí tự có số lần xuất hiện **không nhỏ hơn** $k$ trong dãy trên theo thứ tự từ điển.

## Dữ liệu

Đọc từ tệp văn bản **`KITU.INP`**:
- Dòng đầu chứa hai số nguyên dương $n$ và $k$ cách nhau một khoảng trắng, trong đó $n$ là số lượng kí tự của dãy và $k$ là số lần xuất hiện cần đếm $(1 \le k \le n \le 10^6)$.
- Dòng thứ hai chứa $n$ kí tự là chữ cái Latinh in hoa viết liền nhau.

## Kết quả

Ghi ra tệp văn bản **`KITU.OUT`** một dãy các kí tự có số lần xuất hiện không nhỏ hơn $k$ và được sắp xếp theo thứ tự từ điển. Trường hợp không có kí tự nào thỏa mãn thì ghi một số $0$.

## Ví dụ

| KITU.INP | KITU.OUT |
|---|---|
| `10 3`<br>`CABADDABDD` | `AD` |

*Giải thích: `A` xuất hiện $3$ lần, `D` xuất hiện $4$ lần (đều $\ge 3$); `B` xuất hiện $2$ lần, `C` xuất hiện $1$ lần (đều $< 3$).*

## Ràng buộc

- Subtask 1 ($20\%$ số điểm): $1 \le k \le n < 10^2$.
- Subtask 2 ($40\%$ số điểm): $10^2 \le k \le n < 10^4$.
- Subtask 3 ($40\%$ số điểm): $10^4 \le k \le n \le 10^6$.
