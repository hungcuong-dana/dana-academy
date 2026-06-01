## Đề bài

Cho một xâu $S$ chỉ bao gồm các chữ cái in thường, có độ dài tối thiểu $2$ và tối đa $250$ ký tự.

**Yêu cầu:** Hãy viết chương trình tạo ra xâu $M$ từ xâu $S$ bằng cách xóa các ký tự liên tiếp giống nhau trong xâu $S$ và chỉ để lại một ký tự đại diện trong đoạn đó (nếu một đoạn có nhiều hơn $1$ ký tự liên tiếp giống nhau thì chỉ giữ lại $1$ ký tự trong đoạn đó).

## Dữ liệu

Đọc từ tệp văn bản **`RUTGON.INP`** gồm một dòng duy nhất chứa xâu $S$ chỉ bao gồm các chữ cái in thường.

## Kết quả

Ghi ra tệp văn bản **`RUTGON.OUT`** gồm một dòng duy nhất là xâu $M$ tìm được.

## Ví dụ

| RUTGON.INP | RUTGON.OUT |
|---|---|
| `aaabbbaac` | `abac` |
| `xxyyzzx` | `xyzx` |

## Ràng buộc

- Subtask 1 ($30\%$ số điểm): $|S| \le 20$.
- Subtask 2 ($30\%$ số điểm): $|S| \le 120$.
- Subtask 3 ($40\%$ số điểm): $|S| \le 250$.
