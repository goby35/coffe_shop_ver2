from backend import create_app
from backend.models import User, db

app = create_app()
with app.app_context():
    # Tạo tài khoản admin
    admin = User(
        name='Admin',  # Thêm tên
        email='hongngoc30524@gmail.com',
        is_admin=True
    )
    admin.set_password('123456')  # Đặt mật khẩu
    db.session.add(admin)
    db.session.commit()
    print("Đã tạo tài khoản admin thành công!") 