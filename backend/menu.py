from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from .models import Item, Category, User, PriceItem
from flask_login import login_required, current_user
from functools import wraps
from flask import abort
import os
from . import db
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime

menu = Blueprint('menu', __name__)

# Thư mục lưu ảnh
UPLOAD_FOLDER = os.path.join('backend', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)
        else:
            abort(403)
    return wrap

def formatCurrency(value):
    return f"{value:,.0f} VNĐ"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(image):
    if image and allowed_file(image.filename):
        filename = secure_filename(image.filename)
        ext = filename.rsplit('.', 1)[1]
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        image_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        image.save(image_path)
        return f"/static/uploads/{unique_filename}"
    return None

@menu.route('/menu')
@admin_required
@login_required
def menu_page():
    categories = Category.query.all()
    items = Item.query.all()
    items_with_prices = []
    for item in items:
        latest_price = PriceItem.query.filter_by(item_id=item.id)\
            .order_by(PriceItem.updated_date.desc())\
            .first()
        items_with_prices.append({
            'item': item,
            'latest_price': latest_price or PriceItem(price=0, updated_date=datetime.now()) # Giá trị mặc định 0 nếu không có giá
        })
    return render_template("menu.html", 
                         user=current_user, 
                         formatCurrency=formatCurrency, 
                         categories=categories, 
                         items=items_with_prices)

@menu.route('/categories', methods=['POST', 'GET'])
@login_required
@admin_required
def manage_category():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name')
            if not name or len(name) < 1:
                flash('Tên danh mục không được để trống', 'error')
            else:
                new_category = Category(name=name)
                db.session.add(new_category)
                db.session.commit()
                flash('Đã thêm danh mục thành công', 'success')
        elif action == 'delete':
            category_id = request.form.get('category_id')
            category = Category.query.get(category_id)
            if category:
                db.session.delete(category)
                db.session.commit()
                flash('Đã xóa danh mục thành công', 'success')
        return redirect(url_for('menu.menu_page'))
    
    categories = Category.query.all()
    items = Item.query.all()
    items_with_prices = []
    for item in items:
        latest_price = PriceItem.query.filter_by(item_id=item.id)\
            .order_by(PriceItem.updated_date.desc())\
            .first()
        items_with_prices.append({
            'item': item,
            'latest_price': latest_price
        })
    return render_template('menu.html', 
                         user=current_user, 
                         categories=categories, 
                         items=items_with_prices, 
                         formatCurrency=formatCurrency)

# API endpoints cho MenuItem
@menu.route('/manage_item', methods=['GET', 'POST'])
def manage_item():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name')
            price = request.form.get('price')
            category_id = request.form.get('category_id')
            image = request.files.get('image')
            
            if not name or len(name) < 1:  
                flash('Tên món không hợp lệ', 'error')
            elif not price or not category_id:
                flash('Thiếu thông tin bắt buộc', 'error')
            else:
                try:
                    # Tạo item mới
                    new_item = Item(name=name, category_id=category_id)
                    db.session.add(new_item)
                    db.session.flush()  # Để lấy id của item mới
                    
                    # Tạo price record đầu tiên
                    current_time = datetime.now()
                    new_price = PriceItem(
                        item_id=new_item.id,
                        updated_date=current_time,
                        price=float(price)
                    )
                    db.session.add(new_price)
                    
                    # Xử lý ảnh nếu có
                    if image:
                        image_url = save_image(image)
                        new_item.image_url = image_url
                    
                    db.session.commit()
                    flash('Đã thêm món thành công', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Lỗi khi thêm món: {str(e)}', 'error')
                    
        elif action == 'delete':
            item_id = request.form.get('item_id')
            item = Item.query.get(item_id)
            if item:
                try:
                    # Xóa tất cả các bản ghi giá liên quan
                    PriceItem.query.filter_by(item_id=item_id).delete()
                    
                    # Xóa món
                    db.session.delete(item)
                    db.session.commit()
                    return jsonify({'success': True})
                except Exception as e:
                    db.session.rollback()
                    return jsonify({'success': False, 'error': str(e)})
            return jsonify({'success': False, 'error': 'Không tìm thấy món'})
            
        elif action == 'update':
            item_id = request.form.get('item_id')
            item = Item.query.get(item_id)
            if item:
                try:
                    new_price = request.form.get('price')
                    if new_price:
                        try:
                            new_price = float(new_price)
                        except ValueError:
                            return jsonify({'success': False, 'error': 'Giá không hợp lệ'})
                        current_time = datetime.now()
                        new_price_record = PriceItem(
                            item_id=item_id,
                            updated_date=current_time,
                            price=new_price
                        )
                        db.session.add(new_price_record)
                        db.session.commit()
                        return jsonify({'success': True})
                    return jsonify({'success': False, 'error': 'Không có giá mới'})
                except Exception as e:
                    db.session.rollback()
                    return jsonify({'success': False, 'error': str(e)})
            return jsonify({'success': False, 'error': 'Không tìm thấy món'})    
    return redirect(url_for('menu.menu_page'))
    
    # Lấy danh sách items với giá mới nhất
    items = Item.query.all()
    items_with_prices = []
    for item in items:
        latest_price = PriceItem.query.filter_by(item_id=item.id)\
            .order_by(PriceItem.updated_date.desc())\
            .first()
        items_with_prices.append({
            'item': item,
            'latest_price': latest_price
        })
    
    return render_template('menu.html', 
                         user=current_user,
                         items=items_with_prices,
                         categories=Category.query.all(),
                         formatCurrency=formatCurrency)
            
