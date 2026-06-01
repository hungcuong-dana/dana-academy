## Đề bài

Lam là một học sinh giỏi môn Tin học. Hôm nay các bạn nhờ Lam một bài toán về xâu như sau: Cho xâu $S$ chỉ gồm các kí tự chữ cái in thường, các kí tự trong xâu $S$ được đánh số thứ tự từ $1$ đến $|S|$ (trong đó $|S|$ là độ dài của xâu $S$) và thực hiện $m$ lần thay đổi. Với mỗi lần thay đổi, chọn một số nguyên dương $k$ và đảo ngược một đoạn của xâu $S$ từ vị trí $k$ trở về vị trí $|S| - k + 1$ (luôn đảm bảo $k > \dfrac{|S|}{2}$).

**Yêu cầu:** Viết chương trình tìm xâu $S$ sau $m$ lần thay đổi.

## Dữ liệu

Đọc từ tệp văn bản **`DAOXAU.INP`** gồm:
- Dòng thứ nhất là xâu $S$ $(2 \le |S| \le 2 \cdot 10^5)$.
- Dòng thứ hai là số nguyên dương $m$ $(1 \le m \le 10^5)$.
- Dòng thứ ba là $m$ số nguyên dương $a_1, a_2, \dots, a_m$ $\left(\dfrac{|S|}{2} < a_i \le |S|;\ i = 1 \dots m\right)$.

## Kết quả

Ghi ra tệp văn bản **`DAOXAU.OUT`** gồm $1$ dòng duy nhất là kết quả của bài toán.

## Ví dụ

| DAOXAU.INP | DAOXAU.OUT | Giải thích |
|---|---|---|
| `abcdef`<br>`3`<br>`5 6 4` | `fbdcea` | Với $k=5$: `abcdef` $\to$ `aedcbf`.<br>Với $k=6$: `aedcbf` $\to$ `fbcdea`.<br>Với $k=4$: `fbcdea` $\to$ `fbdcea`. |

## Ràng buộc

- Subtask 1 ($50\%$ số điểm): $|S| \le 10^3$ và $m \le 10^3$.
- Subtask 2 ($50\%$ số điểm): không có ràng buộc gì thêm.
