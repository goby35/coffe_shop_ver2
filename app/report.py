from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for
from .models import db, Order, OrderStatus, Expense
from datetime import datetime, timedelta
from sqlalchemy import func, extract
import io
import csv
from flask import abort
from flask_login import current_user, login_required    
from functools import wraps
import calendar

report = Blueprint('report', __name__)

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)
        else:
            abort(403)
    return wrap

def formatCurrency(value):
    try:
        # Đảm bảo value là số, nếu không trả về 0 VNĐ
        return f"{float(value):,.0f} VNĐ"
    except (TypeError, ValueError):
        return "0 VNĐ"

@report.route('/report', methods=['GET', 'POST'])
@login_required
@admin_required
def report_page():
    # Khởi tạo các biến mặc định
    filter_type = 'month'
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    stats = []

    if request.method == 'POST':
        filter_type = request.form.get('filter_type')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        if not all([filter_type, start_date, end_date]):
            flash('Vui lòng điền đầy đủ thông tin', 'error')
            return redirect(url_for('report.report_page'))
            
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            flash('Ngày không hợp lệ', 'error')
            return redirect(url_for('report.report_page'))
            
        if filter_type == 'day':
            # Báo cáo theo ngày
            current_date = start_date
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                # Tính doanh thu trong ngày
                revenue = db.session.query(
                    func.sum(Order.total_amount)
                ).filter(
                    Order.order_time >= current_date,
                    Order.order_time < next_date
                ).scalar() or 0
                
                # Tính chi phí trong ngày
                expense = db.session.query(
                    func.sum(Expense.count * Expense.price)
                ).filter(
                    Expense.date_time >= current_date,
                    Expense.date_time < next_date
                ).scalar() or 0
                
                stats.append({
                    'month': current_date.strftime('%d/%m/%Y'),
                    'revenue': float(revenue),
                    'expense': float(expense),
                    'profit': float(revenue - expense)
                })
                
                current_date = next_date
                
        else:
            # Báo cáo theo tháng
            current_date = start_date.replace(day=1)
            while current_date <= end_date:
                next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
                
                # Tính doanh thu trong tháng
                revenue = db.session.query(
                    func.sum(Order.total_amount)
                ).filter(
                    Order.order_time >= current_date,
                    Order.order_time < next_month
                ).scalar() or 0
                
                # Tính chi phí trong tháng
                expense = db.session.query(
                    func.sum(Expense.count * Expense.price)
                ).filter(
                    Expense.date_time >= current_date,
                    Expense.date_time < next_month
                ).scalar() or 0
                
                stats.append({
                    'month': current_date.strftime('%m/%Y'),
                    'revenue': float(revenue),
                    'expense': float(expense),
                    'profit': float(revenue - expense)
                })
                
                current_date = next_month
    
    return render_template('report.html',
                         user=current_user,
                         stats=stats,
                         filter_type=filter_type,
                         start_date=start_date.strftime('%Y-%m-%d'),
                         end_date=end_date.strftime('%Y-%m-%d'))

@report.route('/export_csv', methods=['POST'])
def export_csv():
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    # Tính số liệu thống kê
    start = datetime.strptime(start_date, '%Y-%m-%d').date()
    end = datetime.strptime(end_date, '%Y-%m-%d').date()
    stats = []
    current_date = start.replace(day=1)
    while current_date <= end:
        next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        revenue = db.session.query(
            func.sum(Order.total_amount)
        ).join(OrderStatus).filter(
            OrderStatus.finish_time.isnot(None),
            Order.order_time >= current_date,
            Order.order_time < next_month
        ).scalar() or 0

        expense = db.session.query(
            func.sum(Expense.count * Expense.price)
        ).filter(
            Expense.date_time >= current_date,
            Expense.date_time < next_month
        ).scalar() or 0

        stats.append({
            'month': current_date.strftime('%Y-%m'),
            'revenue': float(revenue),
            'expense': float(expense),
            'profit': float(revenue - expense)
        })
        current_date = next_month

    # Tạo file CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Tháng', 'Doanh thu', 'Chi phí', 'Lợi nhuận'])
    for stat in stats:
        writer.writerow([stat['month'], stat['revenue'], stat['expense'], stat['profit']])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'report_{start_date}_to_{end_date}.csv'
    )