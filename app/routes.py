from flask import Blueprint, jsonify, request
from .models import db, Order, Table
from datetime import datetime

api = Blueprint('api', __name__)

@api.route('/orders', methods=['POST'])
def create_order():
    data = request.json
    try:
        # Tạo đơn hàng mới
        order = Order(
            order_id=data['orderId'],
            table_name=data['tableName'],
            items=data['items'],
            total_amount=data['totalAmount'],
            cashier=data['cashier'],
            status='waiting'
        )
        db.session.add(order)
        
        # Cập nhật trạng thái bàn
        table = Table.query.filter_by(name=data['tableName']).first()
        if table:
            table.status = False  # Đánh dấu bàn đã đặt
            table.current_order_id = order.order_id  # Liên kết với đơn hàng hiện tại
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order': order.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/orders/<order_id>/complete', methods=['PUT'])
def complete_order(order_id):
    try:
        # Tìm đơn hàng và bàn tương ứng
        order = Order.query.filter_by(order_id=order_id).first()
        if not order:
            return jsonify({
                'success': False,
                'error': 'Không tìm thấy đơn hàng!'
            }), 404
            
        table = Table.query.filter_by(current_order_id=order_id).first()
        if not table:
            return jsonify({
                'success': False,
                'error': 'Không tìm thấy bàn cho đơn hàng này!'
            }), 404
            
        data = request.json
        # Cập nhật trạng thái đơn hàng
        order.status = 'completed'
        order.completed_at = datetime.fromisoformat(data['completedAt'].replace('Z', '+00:00'))
        order.completed_by = data['completedBy']
        
        # Cập nhật trạng thái bàn
        table.status = True  # Đánh dấu bàn trống
        table.current_order_id = None  # Xóa liên kết với đơn hàng
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'order': order.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api.route('/orders/table/<table_name>', methods=['GET'])
def get_table_order(table_name):
    try:
        # Tìm bàn và đơn hàng hiện tại
        table = Table.query.filter_by(name=table_name).first()
        if not table:
            return jsonify({
                'success': False,
                'error': 'Không tìm thấy bàn!'
            }), 404
            
        if not table.current_order_id:
            return jsonify({
                'success': False,
                'error': 'Không tìm thấy đơn hàng cho bàn này!'
            }), 404
            
        order = Order.query.filter_by(order_id=table.current_order_id).first()
        if not order or order.status != 'waiting':
            return jsonify({
                'success': False,
                'error': 'Không tìm thấy đơn hàng đang chờ cho bàn này!'
            }), 404
            
        return jsonify({
            'success': True,
            'order': order.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 