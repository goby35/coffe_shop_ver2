from flask import Blueprint, json, request, jsonify, render_template, redirect, url_for
from .models import Order, Table, User, Category, Item, OrderItem, PriceItem, OrderStatus, db
from flask_login import login_required, current_user
from datetime import datetime
import time

order = Blueprint('order', __name__)

#Hiển thị trang đặt hàng
@order.route('/order_management', methods=['GET'])
@login_required
def order_page():
    table_filter = request.args.get('table_filter', 'all')

    # Lấy danh sách bàn
    if table_filter == 'available':
        tables = Table.query.filter(~Table.orders.any(Order.status.has(finish_time=None))).all()
    elif table_filter == 'occupied':
        tables = Table.query.filter(Table.orders.any(Order.status.has(finish_time=None))).all()
    else:
        tables = Table.query.all()

    tables_data = [t.to_dict() for t in tables]

    # Lấy danh sách món
    menu_filter = request.args.get('menu_filter', 'all')
    if menu_filter == 'food':
        items = Item.query.join(Category).filter(Category.name == 'food').all()
    elif menu_filter == 'drink':
        items = Item.query.join(Category).filter(Category.name == 'drink').all()
    else:
        items = Item.query.all()

    menus_data = []
    for item in items:
        latest_price = PriceItem.query.filter_by(item_id=item.id)\
            .order_by(PriceItem.updated_date.desc())\
            .first()
        item_dict = item.to_dict()
        item_dict['price'] = latest_price.price if latest_price else 0
        menus_data.append(item_dict)

    user_data = {
        'id': current_user.id,
        'name': current_user.name,
        'email': current_user.email
    }

    return render_template('order_management.html',
                         tables=tables_data,
                         menus=menus_data,
                         table_filter=table_filter,
                         menu_filter=menu_filter,
                         user=user_data)

#Lọc bàn theo trạng thái
@order.route('/filter_table', methods=['GET'])
@login_required
def filter_table():
    table_filter = request.args.get('table_filter', 'all')
    if table_filter == 'available':
        tables = Table.query.filter(~Table.orders.any()).all()
    elif table_filter == 'occupied':
        tables = Table.query.filter(Table.orders.any()).all()
    else:
        tables = Table.query.all()
    return jsonify({'tables': [t.to_dict() for t in tables]})

#Lọc món theo danh mục
@order.route('/filter_item', methods=['GET'])
@login_required
def filter_item():
    filter_item = request.args.get('filter_item', 'all')
    if filter_item == 'food':
        items = Item.query.join(Category).filter(Category.name == 'food').all()
    elif filter_item == 'drink':
        items = Item.query.join(Category).filter(Category.name == 'drink').all()
    else:
        items = Item.query.all()

    # Lấy giá mới nhất của mỗi món
    items_with_prices = []
    for item in items:
        latest_price = PriceItem.query.filter_by(item_id=item.id)\
            .order_by(PriceItem.updated_date.desc())\
            .first()
        item_dict = item.to_dict()
        item_dict['price'] = latest_price.price if latest_price else 0
        items_with_prices.append(item_dict)

    return jsonify({'menus': items_with_prices})

#Tạo đơn hàng
@order.route('/create_order', methods=['POST'])
@login_required
def create_order():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Không có dữ liệu'}), 400

        # Kiểm tra các trường bắt buộc
        required_fields = ['table_id', 'user_id', 'total_amount', 'order_time', 'items']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'error': 'Thiếu các trường bắt buộc'}), 400

        # Kiểm tra bàn
        table = Table.query.get(data['table_id'])
        if not table:
            return jsonify({'success': False, 'error': f'Không tìm thấy bàn {data["table_id"]}'}), 404
        
        # Kiểm tra trạng thái bàn (trống nếu không có đơn hàng nào chưa hoàn thành)
        if not table.to_dict()['status']:
            return jsonify({'success': False, 'error': 'Bàn đã được đặt'}), 400

        # Kiểm tra items
        if not data['items']:
            return jsonify({'success': False, 'error': 'Chưa chọn món'}), 400

        # Tạo đơn hàng
        new_order = Order(
            table_id=data['table_id'],
            user_id=data['user_id'],
            total_amount=0,  # Sẽ được tính lại
            order_time=datetime.fromisoformat(data['order_time'])
        )
        db.session.add(new_order)
        db.session.flush()

        # Tạo trạng thái đơn hàng (đang chờ)
        order_status = OrderStatus(
            order_id=new_order.id,
            finish_time=None
        )
        db.session.add(order_status)

        # Thêm món và tính lại tổng tiền
        total_amount = 0
        for item in data['items']:
            menu = Item.query.get(item['item_id'])
            if not menu:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Không tìm thấy món {item["item_id"]}'}), 404
            if item['count'] <= 0:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Số lượng không hợp lệ cho món {item["item_id"]}'}), 400

            # Kiểm tra giá
            latest_price = PriceItem.query.filter_by(item_id=menu.id)\
                .order_by(PriceItem.updated_date.desc())\
                .first()
            if not latest_price or item['price'] != latest_price.price:
                db.session.rollback()
                return jsonify({'success': False, 'error': f'Giá không hợp lệ cho món {item["item_id"]}'}), 400

            order_item = OrderItem(
                order_id=new_order.id,
                item_id=item['item_id'],
                count=item['count']
            )
            db.session.add(order_item)
            total_amount += latest_price.price * item['count']

        # Kiểm tra tổng tiền
        if abs(total_amount - data['total_amount']) > 0.01:
            db.session.rollback()
            return jsonify({'success': False, 'error': 'Tổng tiền không khớp'}), 400
        new_order.total_amount = total_amount

        db.session.commit()

        return jsonify({
            'success': True,
            'order_id': new_order.id,
            'message': 'Tạo đơn hàng thành công'
        })

    except ValueError as ve:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Lỗi định dạng dữ liệu: {str(ve)}'}), 400
    except db.exc.IntegrityError as ie:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Lỗi cơ sở dữ liệu: Bàn hoặc người dùng không hợp lệ'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Lỗi server: {str(e)}'}), 500

#Thêm món vào đơn hàng
@order.route('/add_item', methods=['POST'])
def add_item():
    order_id = request.form.get('order_id')
    menu_item_id = request.form.get('menu_item_id')
    quantity = int(request.form.get('quantity', 1))  # Mặc định là 1 nếu không cung cấp

    order = Order.query.get(order_id)
    menu_item = Item.query.get(menu_item_id)

    if not order or not menu_item:
        return jsonify({'error': 'Đơn hàng hoặc món không tồn tại'}), 400
    order.add_item(menu_item, quantity)
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

#Hoàn thành đơn hàng
@order.route('/complete_order', methods=['POST'])
@login_required
def complete_order():
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        
        if not order_id:
            return jsonify({'success': False, 'error': 'Order ID is required'}), 400
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
        
        # Cập nhật trạng thái đơn hàng
        order_status = OrderStatus.query.get(order_id)
        if not order_status:
            return jsonify({'success': False, 'error': 'Order status not found'}), 404
            
        order_status.finish_time = datetime.fromisoformat(data['finish_time'])
        
        # Cập nhật trạng thái bàn
        table = Table.query.get(order.table_id)
        if table:
            # Kiểm tra xem bàn có đơn hàng chưa hoàn thành nào khác không
            has_other_active_order = Order.query.filter_by(table_id=table.id)\
                .join(OrderStatus)\
                .filter(OrderStatus.finish_time.is_(None))\
                .filter(Order.id != order_id)\
                .first() is not None
            if not has_other_active_order:
                table.status = True  # Đánh dấu bàn là trống nếu không có đơn hàng khác
                
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Order completed successfully',
            'finish_time': order_status.finish_time.isoformat()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@order.route('/api/orders/<order_id>/complete', methods=['PUT'])
@login_required
def complete_order_api(order_id):
    try:
        data = request.get_json()
        
        # Tìm đơn hàng
        order = Order.query.filter_by(id=order_id).first()
        if not order:
            return jsonify({'error': 'Không tìm thấy đơn hàng'}), 404
            
        # Cập nhật trạng thái đơn hàng
        order.status = 'completed'
        order.completed_at = data.get('completedAt')
        order.completed_by = data.get('completedBy')
        
        # Cập nhật trạng thái bàn
        if order.table:
            order.table.status = True  # Đánh dấu bàn là trống
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order': order.to_dict(),
            'message': 'Đã hoàn thành đơn hàng'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': f'Lỗi khi hoàn thành đơn hàng: {str(e)}'
        }), 500

import logging
logging.basicConfig(level=logging.DEBUG)

@order.route('/api/tables', methods=['GET'])
@login_required
def get_all_tables():
    try:
        tables = Table.query.all()
        return jsonify({
            'success': True,
            'tables': [{
                'id': table.id,
                'name': table.name,
                'status': table.to_dict()['status']
            } for table in tables]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@order.route('/api/orders/table/<table_name>', methods=['GET'])
@login_required
def get_order_by_table(table_name):
    start_time = time.time()
    try:
        # Kiểm tra định dạng tên bàn
        if not table_name or not isinstance(table_name, str):
            return jsonify({
                'success': False, 
                'error': 'Tên bàn không hợp lệ',
                'response_time': f"{(time.time() - start_time) * 1000:.2f}ms"
            }), 400

        # Tìm bàn
        table = Table.query.filter_by(name=table_name).first()
        if not table:
            return jsonify({
                'success': False, 
                'error': f'Không tìm thấy bàn {table_name}',
                'response_time': f"{(time.time() - start_time) * 1000:.2f}ms"
            }), 404

        # Tìm đơn hàng đang chờ
        order = Order.query.filter_by(table_id=table.id)\
            .join(OrderStatus)\
            .filter(OrderStatus.finish_time.is_(None))\
            .first()

        if not order:
            return jsonify({
                'success': False, 
                'error': 'Không có đơn hàng đang chờ cho bàn này',
                'response_time': f"{(time.time() - start_time) * 1000:.2f}ms"
            }), 200  # Thay đổi status code từ 404 thành 200

        # Lấy danh sách món trong đơn hàng
        order_items = OrderItem.query.filter_by(order_id=order.id).all()
        items = []
        for item in order_items:
            menu = Item.query.get(item.item_id)
            if not menu:
                continue
                
            latest_price = PriceItem.query.filter_by(item_id=menu.id)\
                .order_by(PriceItem.updated_date.desc())\
                .first()
            items.append({
                'item_id': item.item_id,
                'name': menu.name,
                'count': item.count,
                'price': latest_price.price if latest_price else 0,
                'image_url': menu.image_url
            })

        response_time = (time.time() - start_time) * 1000  # Chuyển sang milliseconds
        return jsonify({
            'success': True,
            'order': {
                'id': order.id,
                'table_id': order.table_id,
                'table_name': table.name,
                'total_amount': order.total_amount,
                'order_time': order.order_time.isoformat(),
                'status': order.status.to_dict() if order.status else None,
                'items': items
            },
            'response_time': f"{response_time:.2f}ms"
        })

    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e),
            'response_time': f"{(time.time() - start_time) * 1000:.2f}ms"
        }), 500