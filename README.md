# vietfrontier

Tối ưu danh mục chứng khoán Việt Nam trong terminal bằng `vnstock`: lấy dữ liệu giá lịch sử, chạy chạy thuật toán tối ưu, rồi hiển thị **đường biên hiệu quả**, và trực quan hoá các danh mục kém hiệu quả bằng **mô phỏng Monte Carlo** , điểm tối ưu, và tỷ trọng danh mục chứng khoán ngay trên terminal.

`VietFrontier` hướng tới trở thành công cụ nghiên cứu danh mục cổ phiếu Việt Nam chạy trong terminal, giúp cộng đồng Python và `vnstock` thử nghiệm các chiến lược phân bổ danh mục một cách nhanh chóng và trực quan.

![questionary](https://img.shields.io/badge/questionary-2.1.0-blue)
![vnstock](https://img.shields.io/badge/vnstock-3.x-green)

## `vietfrontier` dành cho ai?

`VietFrontier` được thiết kế cho cộng đồng đang sử dụng **`vnstock` và Python để phân tích cổ phiếu Việt Nam**.

### Nhà đầu tư cá nhân có nền tảng kỹ thuật

Những người đã quen sử dụng Python hoặc script để phân tích cổ phiếu thay vì chỉ dùng app trading.

Phù hợp với:

- nhà đầu tư cá nhân muốn phân bổ tiền vào nhiều cổ phiếu theo cách có hệ thống
- môi giới chứng khoán hoặc người tư vấn đầu tư muốn minh họa logic phân bổ danh mục rõ ràng hơn cho khách hàng

### Trader / nhà đầu tư thích phân tích định lượng

Những người quan tâm tới:

- diversification
- Sharpe ratio
- volatility
- risk-adjusted return

### Sinh viên tài chính / quantitative finance

Những người đang học:

- Portfolio theory
- Efficient frontier
- Asset allocation

## Vì sao cần tối ưu phân bổ danh mục?

Khi đầu tư vào nhiều cổ phiếu trong cùng một rổ, điều quan trọng không chỉ là mã nào tăng mạnh hơn, mà còn là **bạn đã phân bổ bao nhiêu vốn vào từng mã**.

Ví dụ:

- một cổ phiếu lãi `100%` nhưng bạn chỉ phân bổ `1 triệu đồng`
- một cổ phiếu khác lỗ `5%` nhưng bạn phân bổ tới `300 triệu đồng`

Trong trường hợp đó, tổng kết quả danh mục vẫn có thể kém vì phần vốn lớn đang nằm ở vị thế có hiệu quả thấp hơn. Điều này cho thấy nhìn vào phần trăm tăng giảm của từng mã riêng lẻ là chưa đủ; bạn cần nhìn cả **tỷ trọng vốn, lợi nhuận kỳ vọng, và mức rủi ro của toàn danh mục**.

`VietFrontier` giúp bạn thử nhanh các cách phân bổ khác nhau để quan sát mối quan hệ giữa:

- lợi nhuận kỳ vọng
- biến động
- tỷ lệ Sharpe
- tỷ trọng vốn theo từng mã

## `vietfrontier` làm được gì?

- Nhận nhiều mã cổ phiếu Việt Nam trong một lần chạy, ví dụ `ACB,VCB,FPT,HPG,MWG`.
- Tải lịch sử giá đóng cửa ngày từ `vnstock` qua nguồn `VCI` hoặc `KBS`.
- Tối ưu danh mục với các objective: `max_sharpe`, `min_volatility`, `max_quadratic_utility`.
- Cho phép chọn `return model` và `risk model` cho các bài toán mean-variance.
- Vẽ `efficient frontier`, `Monte Carlo` cloud, và điểm tối ưu ngay trong terminal bằng `plotext`.
- In bảng tỷ trọng và hiệu suất danh mục bằng `rich`.

## Demo

<!-- TODO: Add terminal GIF or screenshot showing: prompt flow -> frontier chart -> weights/performance tables -->

Sau khi khởi chạy thành công, bạn sẽ thấy:

- prompt để nhập mã, nguồn dữ liệu, khoảng thời gian `start date` và `end date`, `objective`, return/risk model, và các tham số tối ưu.
- biểu đồ terminal-native:
  `efficient frontier` + `Monte Carlo` + điểm tối ưu cho các objective mean-variance.
- biểu đồ cột tỷ trọng cho `hrp`nếu chọn chiến lược tối ưu là **HRP**
- Báo cáo được trình bày ngay trên terminal :
  weights theo mã và performance của danh mục.

## Cài đặt

Yêu cầu:

- Python `3.13+`
- `uv`

Thiết lập môi trường:

```bash
uv sync
```

## Chạy ứng dụng

```bash
uv run vietfrontier
```

Hoặc:

```bash
uv run python main.py
```

## Quick Start

1. Chạy app:

```bash
uv run vietfrontier
```

2. Trả lời các prompt trong terminal. Mặc định app đã gợi ý sẵn một rổ mã:

```text
ACB,VCB,FPT,HPG,MWG
```

3. Sau khi nhập xong, app sẽ:

- tải dữ liệu giá ngày bằng `vnstock`
- tối ưu danh mục theo objective bạn chọn
- hiển thị chart trong terminal
- in bảng tỷ trọng và bảng performance

## Prompt Flow

Trong một phiên chạy, `vietfrontier` hiện hỗ trợ đúng các lựa chọn sau:

- `Symbols (comma-separated)`
- `Source`: `VCI` hoặc `KBS`
- `Start date (YYYY-MM-DD)`
- `End date (YYYY-MM-DD)`
- `Objective`:
  `max_sharpe`, `min_volatility`, `max_quadratic_utility`, `hrp`
- Với các objective mean-variance:
  - `Return method`:
    `mean_historical`, `ema_historical`
  - `Use log returns`:
    `yes` hoặc `no`
  - `EMA smoothing span` khi chọn `ema_historical`
  - `Risk model`:
    `sample_cov`, `exp_cov`, `semicovariance`, `ledoit_wolf`, `oracle_approximating`
- `Scatter colormap` cho Monte Carlo cloud:
  `copper`, `gist_heat`, `Greys`, `gist_yarg`, `gist_gray`, `cividis`, `magma`, `inferno`, `plasma`, `viridis`
- `Risk-free rate`
- `Risk aversion (δ)` khi chọn `max_quadratic_utility`
- `Simulated portfolios`

Lưu ý:

- `hrp` không dùng `efficient frontier` scatter plot. Ở mode này app sẽ hiển thị biểu đồ thanh ngang tỷ trọng.
- `hrp` cũng không prompt `return model` hoặc `risk model` riêng như các objective mean-variance.

## Chọn nguồn dữ liệu

`vietfrontier` hiện cho phép chọn một trong hai nguồn mà `vnstock` hỗ trợ trong app này:

| Source | Khi nào nên dùng                                         | Ghi chú                                  |
| ------ | -------------------------------------------------------- | ---------------------------------------- |
| `VCI`  | Mặc định cho hầu hết lần chạy local                      | Đây là lựa chọn mặc định trong prompt    |
| `KBS`  | Khi bạn muốn thử nguồn thay thế ngay trong cùng workflow | App vẫn giữ nguyên flow tối ưu và render |

## Kết quả hiển thị

### 1. Với `max_sharpe`, `min_volatility`, `max_quadratic_utility`

App hiển thị một chart terminal gồm:

- `Monte Carlo` cloud của các danh mục ngẫu nhiên
- đường `efficient frontier`
- điểm `Optimal`

Sau chart là hai bảng:

- `Portfolio Weights`
- `Performance`

### 2. Với `hrp`

App hiển thị:

- biểu đồ thanh ngang tỷ trọng các mã trong terminal

Sau đó vẫn in:

- `Portfolio Weights`
- `Performance`

## Các ràng buộc dữ liệu cần biết

- Cần ít nhất `2` mã để chạy tối ưu danh mục.
- Cần ít nhất `30` ngày giao dịch đồng bộ sau khi ghép các chuỗi giá.
- App hiện dùng dữ liệu `interval="1D"` từ `vnstock`.
- Dữ liệu đầu vào cần có cột `time` và `close` từ provider response.

## Troubleshooting / Các lỗi hay gặp

### Chỉ nhập 1 mã

Chỉ cần nhập lại từ 3 mã trở lên.

### Không đủ số ngày giao dịch đồng bộ

Nếu app báo:

```text
Need at least 30 aligned trading days
```

Ý nghĩa:
sau khi ghép các mã theo ngày giao dịch chung, dữ liệu còn lại quá ngắn để tối ưu ổn định.

Bạn nên làm gì:

- mở rộng khoảng thời gian của dữ liệu lịch sử
- dùng các mã có lịch sử giao dịch đồng đều hơn
- kiểm tra lại source đã chọn

Mức độ đáng lo:
đáng quan tâm ở mức dữ liệu đầu vào; đây không phải crash hệ thống mà là dữ liệu chưa đủ cho bài toán.

### Lỗi tối ưu hóa không khả thi

Nếu app báo `OptimizationError`, nghĩa là bài toán hiện tại không tìm được nghiệm khả thi với dữ liệu và cấu hình bạn đã chọn.

Bạn nên làm gì:

- đổi objective
- đổi `risk model`
- đổi `return model`
- mở rộng khoảng dữ liệu đầu vào

Mức độ đáng lo:
đây là lỗi nghiệp vụ của bài toán tối ưu, không nhất thiết là bug của chương trình.

## Acknowledgements

Dự án sử dụng [vnstock](https://github.com/thinh-vu/vnstock) để tải dữ liệu chứng khoán Việt Nam.
Vui lòng tuân thủ [điều khoản sử dụng](https://github.com/thinh-vu/vnstock?tab=License-1-ov-file#readme) của vnstock khi sử dụng dữ liệu.

## Disclaimer

`vietfrontier` chỉ phục vụ mục đích nghiên cứu và học tập cá nhân, không phải lời khuyên đầu tư.
Dữ liệu từ `vnstock` phụ thuộc nguồn công khai và có thể không chính xác hoặc không đầy đủ.
