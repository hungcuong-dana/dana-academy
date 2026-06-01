## Đề bài

Cho một xâu kí tự $S$ chỉ gồm các chữ cái La-tinh in thường từ `a` đến `z`. Một xâu con $X$ (gồm các kí tự ở vị trí liên tiếp) của $S$ được gọi là một **xâu có tần số xuất hiện cao** nếu trong xâu $X$ có một kí tự bất kỳ nào đó mà số lần xuất hiện của kí tự đó **nhiều hơn** tổng số lần xuất hiện của các kí tự còn lại trong xâu $X$.

Ví dụ: Xâu $S = $ `abbbabced`, xâu con $X = $ `abbbabc` là một xâu có tần số xuất hiện cao, vì có kí tự `b` xuất hiện $4$ lần, tổng số lần xuất hiện các kí tự còn lại bằng $3$ (`a` xuất hiện $2$ lần, `c` xuất hiện $1$ lần). Nếu $X = $ `abbbabce` thì kí tự `b` xuất hiện nhiều lần nhất là $4$ lần và tổng số lần xuất hiện của các kí tự còn lại bằng $4$; do vậy xâu $X = $ `abbbabce` **không phải** là một xâu có tần số xuất hiện cao.

**Yêu cầu:** Tìm xâu con $X$ (gồm các kí tự ở vị trí liên tiếp) của $S$ là một xâu có tần số xuất hiện cao và có độ dài lớn nhất.

## Dữ liệu

Đọc từ tệp văn bản **`TANSO.INP`** gồm một xâu $S$ chỉ gồm các kí tự chữ cái La-tinh in thường và có độ dài không lớn hơn $2 \cdot 10^5$.

## Kết quả

Ghi ra tệp văn bản **`TANSO.OUT`** một số nguyên duy nhất là độ dài của xâu $X$ tìm được.

## Ví dụ

| TANSO.INP | TANSO.OUT | Giải thích |
|---|---|---|
| `aaa` | `3` | Chọn $X = $ `aaa`. |
| `ababab` | `5` | Chọn $X = $ `ababa` (`a` xuất hiện $3$ lần, còn lại $2$). |

## Ràng buộc

- Subtask 1 ($30\%$ số điểm): $S$ chỉ gồm các kí tự thuộc tập $\{$`a`, `b`, `c`$\}$ và $|S| \le 2 \cdot 10^3$.
- Subtask 2 ($30\%$ số điểm): $S$ gồm các kí tự chữ cái La-tinh in thường và $|S| \le 2 \cdot 10^3$.
- Subtask 3 ($40\%$ số điểm): $S$ gồm các kí tự chữ cái La-tinh in thường và $|S| \le 2 \cdot 10^5$.
