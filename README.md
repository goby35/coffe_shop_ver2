project_root/
│── backend/
│   ├── static/          # Chứa file CSS, JS, ảnh được build từ Vite
│   ├── templates/       # Chứa file HTML
│   ├── __init__.py      # Khởi tạo Flask app
│   ├── auth.py          # Xử lý xác thực (login, register)
│   ├── menu.py          # Xử lý menu (thêm, sửa, xóa)
│   ├── models.py        # Chứa các model SQLAlchemy
│   ├── views.py         # Xử lý logic chung (dashboard, home)
│
│── instance/            # Lưu database SQLite (nếu có)
│── main.py              # Chạy Flask app
│── requirements.txt     # Danh sách thư viện
│── config.py            # Cấu hình ứng dụng
│── .env                 # Biến môi trường
│── .gitignore
│── README.md
│
│── frontend/            # Thư mục chứa dự án Vue.js với Vite
│   ├── src/             # Chứa mã nguồn Vue.js
│   ├── public/          # Chứa các file tĩnh công khai
│   ├── index.html       # File HTML chính của Vue.js
│   ├── vite.config.js   # Cấu hình Vite
│   ├── package.json     # Danh sách thư viện và script của Vue.js
│   ├── .gitignore
│   ├── README.md