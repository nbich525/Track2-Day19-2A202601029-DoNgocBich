# Chạy Lab 19 trên Windows với Docker Desktop

Tài liệu này dùng PowerShell mở từ Start Menu hoặc Windows Terminal. Không cần `make`, Bash hay terminal tích hợp VS Code.

## Điều kiện

- Docker Desktop đang mở và báo **Engine running**.
- Python 3.10–3.14 đã cài và lệnh `py` hoạt động.
- RAM trống khoảng 8 GB.
- Các port `6333`, `6334`, `6379`, `5432`, `8000`, `8888` chưa bị chương trình khác dùng.

## Cài đặt lần đầu

```powershell
Set-Location "D:\Vin\Track2-Day19-2A202601029-DoNgocBich"
docker compose up -d

docker compose ps
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-full.txt

.\.venv\Scripts\python.exe scripts\seed_corpus.py
.\.venv\Scripts\python.exe scripts\gen_agent_queries.py
.\.venv\Scripts\python.exe scripts\gen_spend.py
.\.venv\Scripts\python.exe scripts\verify_docker.py
```

Lần đầu chạy `gen_agent_queries.py` và embedding model có thể mất vài phút.
Nếu máy chỉ có Python 3.14, thay `py -3.13` bằng `py -3.14`; dependency đã có
cấu hình override trong file `overrides-py314.txt` nhưng lệnh PowerShell thủ
công có thể cần thêm:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade "dill>=0.4,<1.0"
```

## Chạy API

Giữ PowerShell hiện tại để chạy lệnh hoặc mở một PowerShell khác:

```powershell
Set-Location "D:\Vin\Track2-Day19-2A202601029-DoNgocBich"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở trình duyệt tại:

- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/healthz`
- Ví dụ: `http://localhost:8000/search?q=cloud%20security&mode=hybrid`

`.env` được ứng dụng tự đọc. Để Docker dùng Qdrant server và bge-m3, kiểm tra
các dòng `QDRANT_MODE=server`, `QDRANT_URL=http://localhost:6333` và
`EMBEDDING_BACKEND=bge-m3` trong `.env`. Model bge-m3 lớn; nếu muốn nhẹ hơn,
đặt `EMBEDDING_BACKEND=fastembed` rồi chạy lại index/notebook.

Ứng dụng tự lưu model fastembed vào `.cache\fastembed` trong repo. Cách này
tránh lỗi `WinError 1314` thường gặp khi Hugging Face cố tạo symlink trong
`AppData\Local\Temp`; không cần chạy PowerShell bằng Administrator.

## Chạy notebooks

Mở PowerShell thứ hai:

```powershell
Set-Location "D:\Vin\Track2-Day19-2A202601029-DoNgocBich"
.\.venv\Scripts\jupyter.exe lab --notebook-dir=notebooks --ServerApp.token=""
```

Mở `http://localhost:8888/lab`, rồi chạy lần lượt `01` đến `08`. NB4 cần
`feast apply` và `materialize-incremental`; notebook tự thực hiện hai lệnh đó.

## Chạy bonus

```powershell
Set-Location "D:\Vin\Track2-Day19-2A202601029-DoNgocBich"
.\.venv\Scripts\python.exe bonus\demo.py
```

## Dừng hoặc reset Docker

Giữ dữ liệu và chỉ dừng container:

```powershell
docker compose down
```

Dừng và xóa toàn bộ volume Qdrant, Redis, Postgres:

```powershell
docker compose down -v
```

Khởi động lại:

```powershell
docker compose up -d
```

## Xử lý lỗi thường gặp

- `docker is not recognized`: mở Docker Desktop, rồi mở PowerShell mới để PATH được cập nhật.
- `port is already allocated`: dùng `docker compose down`, hoặc tìm tiến trình chiếm port bằng `Get-NetTCPConnection -LocalPort 6333,6379,5432`.
- `verify_docker.py` báo Qdrant/Redis/Postgres chưa sẵn sàng: chờ các container healthy rồi chạy lại lệnh verify.
- Model bge-m3 tải quá lâu hoặc thiếu RAM: đổi `.env` sang `EMBEDDING_BACKEND=fastembed`, xóa collection cũ bằng `docker compose down -v`, rồi seed/index lại.
- `py -3.13` không tồn tại: chạy `py -0p` để xem phiên bản Python đã cài và dùng đúng hậu tố.
