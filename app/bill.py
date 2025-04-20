from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required
from functools import wraps
from flask import abort
from datetime import datetime
from sqlalchemy.sql import text, func

try:
    from .models import db, Order, OrderItem, Item, PriceItem, Table
except Exception as e:
    with open('debug.txt', 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now()}: ERROR: Lỗi import mô hình: {e}\n")
    raise

bill = Blueprint('bill', __name__)

def debug_to_file(message):
    try:
        with open('debug.txt', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()}: {message}\n")
    except Exception as e:
        print(f"ERROR: Không thể ghi debug.txt: {e}")

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        try:
            user_info = f"current_user: id={current_user.id}, is_admin={getattr(current_user, 'is_admin', None)}"
            debug_to_file(user_info)
            if hasattr(current_user, 'is_admin') and current_user.is_admin:
                return f(*args, **kwargs)
            else:
                debug_to_file("WARNING: Truy cập bị từ chối cho user")
                abort(403)
        except Exception as e:
            debug_to_file(f"ERROR: Lỗi trong admin_required: {e}")
            raise
    return wrap

@bill.route('/bill', methods=['GET', 'POST'])
@login_required
@admin_required
def view_bills():
    debug_to_file("Bắt đầu xử lý yêu cầu view_bills")
    try:
        debug_to_file("Trước khi kiểm tra request.method")
        method = request.method
        debug_to_file(f"Phương thức: {method}")
        
        debug_to_file("Trước khi kiểm tra kết nối cơ sở dữ liệu")
        result = db.session.execute(text("SELECT 1")).scalar()
        debug_to_file(f"Kết nối cơ sở dữ liệu thành công: {result}")
        
        if method == 'POST':
            debug_to_file("Trước khi lấy date_str")
            date_str = request.form.get('date')
            debug_to_file(f"Nhận được date_str: {date_str}")
            
            if not date_str or not isinstance(date_str, str):
                debug_to_file("ERROR: date_str không hợp lệ hoặc rỗng")
                flash('Vui lòng chọn ngày hợp lệ', 'error')
                return redirect(url_for('bill.view_bills'))
                
            debug_to_file("Trước khi chuyển đổi ngày")
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                debug_to_file(f"Đã chuyển đổi date: {date}")
            except ValueError as e:
                debug_to_file(f"ERROR: Lỗi chuyển đổi ngày: {e}")
                flash('Ngày không hợp lệ', 'error')
                return redirect(url_for('bill.view_bills'))
                
            debug_to_file(f"Trước khi truy vấn đơn hàng cho ngày: {date}")
            orders = Order.query.filter(func.date(Order.order_time) == date).all()
            debug_to_file(f"Tìm thấy {len(orders)} đơn hàng")
            
            total_revenue = 0
            bills = []
            
            for order in orders:
                debug_to_file(f"Xử lý đơn hàng: {order.id}")
                try:
                    if not order or not order.order_time or not order.total_amount:
                        debug_to_file(f"WARNING: Bỏ qua đơn hàng không hợp lệ: {order}")
                        continue
                        
                    total_revenue += order.total_amount or 0
                    debug_to_file(f"Trước khi lấy bàn cho đơn hàng {order.id}")
                    table = Table.query.get(order.table_id)
                    debug_to_file(f"Table cho đơn hàng {order.id}: {table}")
                    if not table:
                        debug_to_file(f"WARNING: Không tìm thấy bàn với ID {order.table_id} cho đơn hàng {order.id}")
                        continue
                        
                    items = []
                    debug_to_file(f"Order items type: {type(order.items)}")
                    for item in order.items:
                        debug_to_file(f"Xử lý mục: order_id={item.order_id}, item_id={item.item_id}")
                        try:
                            if not item or not item.item_id or item.count is None:
                                debug_to_file(f"WARNING: Bỏ qua mục không hợp lệ trong đơn hàng {order.id}")
                                continue
                                
                            debug_to_file(f"Trước khi lấy món với ID {item.item_id}")
                            menu_item = Item.query.get(item.item_id)
                            debug_to_file(f"menu_item: {menu_item}")
                            if not menu_item:
                                debug_to_file(f"WARNING: Không tìm thấy món với ID {item.item_id}")
                                continue
                                
                            debug_to_file(f"Trước khi lấy giá cho món {menu_item.id}")
                            price_at_order = PriceItem.query.filter(
                                PriceItem.item_id == menu_item.id,
                                PriceItem.updated_date <= order.order_time
                            ).order_by(PriceItem.updated_date.desc()).first()
                            debug_to_file(f"price_at_order: {price_at_order}")
                            
                            if not price_at_order:
                                debug_to_file(f"WARNING: Không tìm thấy giá cho món {menu_item.id} tại {order.order_time}")
                                price = 0
                            else:
                                price = price_at_order.price
                                
                            def formatCurrency(value):
                                debug_to_file(f"Định dạng tiền tệ: {value}")
                                try:
                                    return f"{float(value):,.0f} VNĐ"
                                except (TypeError, ValueError) as e:
                                    debug_to_file(f"ERROR: Lỗi định dạng tiền tệ: {value}, lỗi: {e}")
                                    return "0 VNĐ"
                            
                            items.append({
                                'name': menu_item.name,
                                'count': item.count or 0,
                                'price': formatCurrency(price),
                                'total': formatCurrency((item.count or 0) * price)
                            })
                        except Exception as item_error:
                            debug_to_file(f"ERROR: Lỗi xử lý mục trong đơn hàng {order.id}: {item_error}")
                            continue
                    
                    debug_to_file(f"Items cho đơn hàng {order.id}: {items}")
                    if items:
                        bill_data = {
                            'order_id': order.id,
                            'order_time': order.order_time,
                            'table_name': table.name if table else 'N/A',
                            'items': items,
                            'total_amount': formatCurrency(order.total_amount or 0)
                        }
                        debug_to_file(f"Bill data cho đơn hàng {order.id}: {bill_data}")
                        bills.append(bill_data)
                        debug_to_file(f"Thêm hóa đơn: order_id={order.id}")
                    else:
                        debug_to_file(f"WARNING: Đơn hàng {order.id} không có mục hợp lệ")
                except Exception as order_error:
                    debug_to_file(f"ERROR: Lỗi xử lý đơn hàng {order.id}: {order_error}")
                    continue
            
            debug_to_file(f"Chuẩn bị render template với {len(bills)} hóa đơn")
            debug_to_file(f"Bills data: {bills}")
            debug_to_file(f"Total revenue: {total_revenue}")
            debug_to_file(f"Formatted total revenue: {formatCurrency(total_revenue)}")
            debug_to_file(f"Date string: {date_str}")
            if not bills:
                flash('Không tìm thấy hóa đơn hợp lệ cho ngày đã chọn', 'info')
                
            debug_to_file(f"Render template: bills={len(bills)}, total_revenue={formatCurrency(total_revenue)}, date={date_str}")
            return render_template('bill.html', 
                                 bills=bills,
                                 total_revenue=formatCurrency(total_revenue),
                                 date=date_str)
                                 
        debug_to_file("Hiển thị template mặc định cho GET")
        return render_template('bill.html')
        
    except Exception as e:
        debug_to_file(f"ERROR: Lỗi trong view_bills: {str(e)}")
        flash('Có lỗi xảy ra khi xử lý yêu cầu', 'error')
        return redirect(url_for('bill.view_bills'))