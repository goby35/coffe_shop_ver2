from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from .models import Order, Table, User, Category, MenuItem
from . import db
from flask_login import login_required, current_user


order = Blueprint('order', __name__)


#Hiển thị trang đặt hàng
@order.route('/order_management', methods=['GET'])
@login_required
def order_page():
    table_filter = request.args.get('table_filter', 'all')
    menu_filter = request.args.get('menu_filter', 'all')

    if table_filter == 'available':
        tables = Table.query.filter_by(status=True).all()
    elif table_filter == 'occupied':
        tables = Table.query.filter_by(status=False).all()
    else:
        tables = Table.query.all()

    if menu_filter == 'food':
        menus = MenuItem.query.filter_by(type='food').all()
    elif menu_filter == 'drink':
        menus = MenuItem.query.filter_by(type='drink').all()
    else:
        menus = MenuItem.query.all()

    return render_template('order_management.html', tables=tables, menus=menus, table_filter=table_filter, menu_filter=menu_filter, user=current_user)

#Lọc bàn theo trạng thái
@order.route('/filter_table', methods=['GET'])
@login_required
def filter_table():
    table_filter = request.args.get('table_filter', 'all')
    if table_filter == 'available':
        tables = Table.query.filter_by(status=True).all()
    elif table_filter == 'occupied':
        tables = Table.query.filter_by(status=False).all()
    else:
        tables = Table.query.all()
    return jsonify({'tables': [t.to_dict() for t in tables]})

#Lọc món theo danh mục
@order.route('/filter_item', methods=['GET'])
@login_required
def filter_item():
    filter_item = request.args.get('filter_item', 'all')
    if filter_item == 'food':
        menus = MenuItem.query.filter_by(category_id=Category.id and Category.name == 'food').all()
    elif filter_item == 'drink':
        menus = MenuItem.query.filter_by(category_id= Category.id and Category.name == 'drink').all()
    else:
        categories = Category.query.all()
    return jsonify({'menus': [m.to_dict() for m in menus]})
#Tạo đơn hàng
@order.route('/create_order', methods=['POST'])
@login_required
def create_order():
    table_id = request.form.get('id')
    table = Table.query.get(table_id) if table_id else None
    order = Order(table=table, user=current_user)
    db.session.add(order)
    db.session.commit()
    return jsonify({'success': True, 'order_id': order.id})

#Thêm món vào đơn hàng
@order.route('/add_item', methods=['POST'])
@login_required
def add_item():
    order_id = request.form.get('id')
    item_id = request.form.get('id')
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Đơn hàng không tồn tại'}), 400
    if not MenuItem.query.get(item_id):
        return jsonify({'error': 'Món không tồn tại'}), 400
    order.add_item(item_id)
    db.session.commit()
    return jsonify({'success': True})

#Xóa món khỏi đơn hàng
@order.route('/remove_item', methods=['POST'])
@login_required
def remove_item():
    order_id = request.form.get('order_id')
    item_id = request.form.get('item_id')
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Đơn hàng không tồn tại'}), 400
    order.remove_item(item_id)
    db.session.commit()
    return jsonify({'success': True})

#Xóa đơn hàng
@order.route('/delete_order', methods=['POST'])
@login_required
def delete_order():
    order_id = request.form.get('order_id')
    order = Order.query.get(order_id)
    db.session.delete(order)
    db.session.commit()
    return jsonify({'success': True})

#Thanh toán đơn hàng
@order.route('/checkout', methods=['POST'])
@login_required
def checkout():
    order_id = request.form.get('order_id')
    order = Order.query.get(order_id)
    order.checkout()
    return jsonify({'success': True})

#Hiển thị trang quản lý đơn hàng
@order.route('/manage_order', methods=['GET'])
@login_required
def manage_order():
    orders = Order.query.all()
    return render_template('manage_order.html', orders=orders)



    