from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .models import MenuItem, Category, User
from flask_login import login_required, current_user
from functools import wraps
from flask import abort
import os
from . import db
from werkzeug.utils import secure_filename
import uuid

menu = Blueprint('menu', __name__)

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)
        else:
            abort(403)
    return wrap

def format_currency(value):
    return "{:,.0f} VND".format(value)

# Thư mục lưu ảnh
UPLOAD_FOLDER = os.path.join('backend', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Tạo thư mục nếu chưa tồn tại
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Kiểm tra file hợp lệ
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(image):
    """ Lưu ảnh và trả về đường dẫn URL đúng """
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        ext = filename.rsplit('.', 1)[1]
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        image_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Lưu ảnh vào thư mục static/uploads/
        image.save(image_path)

        # Trả về đường dẫn có thể truy cập từ trình duyệt
        return f"/static/uploads/{unique_filename}"
    return None


@menu.route('/category', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_category():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            name = request.form.get('name')
            if len(name) < 1:
                flash('Category name must be greater than 1 char.', category='error')
            else:
                new_category = Category(name=name)
                db.session.add(new_category)
                db.session.commit()
                flash("created", category='success')
        if action == 'edit':
            category_id = request.form.get('id')
            category = Category.query.get(category_id)
            if category:
                category.name = request.form.get('name')
                db.session.commit()
                flash('updated', category='success')
            else:
                flash('category not found', category='error')
        if action == 'delete':
            category_id = request.form.get('id')
            category = Category.query.get(category_id)
            if category:
                if category.menu_items:
                    flash("Can't delete category with related items.", category='error')
                else:
                    db.session.delete(category)
                    db.session.commit()
                    flash('category deleted', category='success')
            else:
                flash('category not found', category='error')
        return redirect(url_for('menu.manage_category'))
        
    categories = Category.query.all()
    category_id =request.args.get('id')
    if  category_id:
        items = MenuItem.query.filter_by(category_id=category_id).all()
    else:
            items = MenuItem.query.all()
    return render_template('menu.html', category=categories, item=items, format_currency=format_currency, user=current_user) #
    

@menu.route('/menu_items', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_item():
    try:
        if request.method == 'POST':
            action = request.form.get('action')
            if action == 'create':
                name = request.form.get('item-name')
                price = request.form.get('price')
                cost = request.form.get('cost')
                category_id = request.form.get('category_id')
                image = request.files.get('image')

                if len(name) < 1:
                    flash('Item name >1', category='error')
                else:
                    image_url = save_image(image)
                    new_item = MenuItem(name=name, 
                                            price=float(price), 
                                            cost=float(cost), 
                                            category_id=category_id, 
                                            image_url=image_url
                                        )
                    db.session.add(new_item)
                    db.session.commit()
                    flash('Item created', category='success')
            elif action == 'edit':
                item_id = request.form.get('item_id')
                item = MenuItem.query.get(item_id)
                if item:
                    name = request.form.get('item-name')
                    price = request.form.get('price')
                    cost = request.form.get('cost')
                    category_id = request.form.get('category_id')
                    # Cập nhật ảnh 
                    image = request.files.get('image')
                    print(f"Item ID: {item_id}, Name: {name}, Price: {price}, Cost: {cost}, Category ID: {category_id}, Image: {image}")

                    item = MenuItem.query.get(item_id)
                    if not item:
                        return jsonify(success=False, error="Item not found"), 404

                    item.name = name
                    item.price = float(price)
                    item.cost = float(cost)
                    item.category_id = category_id


                    # Cập nhật đường dẫn ảnh
                    new_image_url = save_image(image)
                    if new_image_url:
                        item.image_url = new_image_url  # Cập nhật URL ảnh mới
                    db.session.commit()
                    flash('Item updated', category='success')
                    return jsonify(success=True, image_url=item.image_url)
                else:
                    return jsonify(success=False, error='Item not found')
            elif action == 'delete':
                item_id = request.form.get('item_id')
                item = MenuItem.query.filter_by(id=item_id).first()
                if item:
                    # # Xóa ảnh nếu tồn tại (tùy chọn)
                    # if item.image_url and os.path.exists(item.image_url[1:]):  # Bỏ '/' đầu tiên
                    #     os.remove(item.image_url[1:])
                    db.session.delete(item)
                    db.session.commit()
                    flash('Item deleted', category='success')
                    return jsonify(success=True)
                else:
                    return jsonify(success=False, error='Item not found')
            return redirect(url_for('menu.manage_item'))
        
        items = MenuItem.query.all()
        categories = Category.query.all()
        return render_template('menu.html', item=items, category=categories,  user=current_user, format_currency=format_currency)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify(success=False, error=str(e)), 500