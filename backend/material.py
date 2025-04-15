from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from .models import Material, Expense, db
from datetime import datetime
import os

material = Blueprint('material', __name__)

@material.route('/material')
@login_required
def materials_page():
    materials = Material.query.all()
    expenses = Expense.query.all()
    return render_template('material.html', materials=materials, expenses=expenses)

# API thêm nguyên liệu
@material.route('/manage_material', methods=['POST'])
@login_required
def manage_material():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name')
            unit = request.form.get('unit')
            
            if not name or len(name) < 1:
                flash('Tên nguyên liệu không hợp lệ', 'error')
            elif not unit:
                flash('Thiếu thông tin đơn vị tính', 'error')
            else:
                try:
                    # Kiểm tra nguyên liệu trùng tên
                    if Material.query.filter_by(name=name).first():
                        flash('Nguyên liệu đã tồn tại', 'error')
                    else:
                        # Tạo nguyên liệu mới
                        material = Material(
                            name=name.strip(),
                            unit=unit.strip(),
                        )
                        db.session.add(material)
                        db.session.commit()
                        flash('Đã thêm nguyên liệu thành công', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Lỗi khi thêm nguyên liệu: {str(e)}', 'error')
                    
        elif action == 'delete':
            material_id = request.form.get('material_id')
            material = Material.query.get(material_id)
            if material:
                try:
                    # Kiểm tra xem nguyên liệu có đang được sử dụng trong chi phí không
                    if material.expenses:
                        flash('Không thể xóa nguyên liệu đang có chi phí', 'error')
                    else:
                        db.session.delete(material)
                        db.session.commit()
                        flash('Xóa nguyên liệu thành công', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Lỗi khi xóa nguyên liệu: {str(e)}', 'error')
            else:
                flash('Không tìm thấy nguyên liệu', 'error')
    
    return redirect(url_for('material.materials_page'))

#thêm đơn nhập hàng
@material.route('/manage_expense', methods=['POST'])
def manage_expense():
    action = request.form.get('action')
    
    if action == 'add':
        try:
            # Chuyển đổi datetime từ string sang đối tượng datetime
            date_time_str = request.form.get('date_time')
            if not date_time_str:
                flash('Vui lòng nhập ngày nhập hàng!', 'error')
                return redirect(url_for('material.materials_page'))
                
            try:
                date_time = datetime.fromisoformat(date_time_str)
            except ValueError:
                flash('Định dạng ngày giờ không hợp lệ!', 'error')
                return redirect(url_for('material.materials_page'))
            
            expense = Expense(
                date_time=date_time,
                material_id=request.form.get('material_id'),
                count=float(request.form.get('count')),
                price=float(request.form.get('price')),

            )
            
            db.session.add(expense)
            db.session.commit()
            flash('Thêm đơn nhập hàng thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi thêm đơn nhập hàng: {str(e)}', 'error')
    
    elif action == 'delete':
        try:
            date_time_str = request.form.get('date_time')
            if not date_time_str:
                flash('Không tìm thấy thông tin ngày giờ!', 'error')
                return redirect(url_for('material.materials_page'))
                
            try:
                date_time = datetime.fromisoformat(date_time_str)
            except ValueError:
                flash('Định dạng ngày giờ không hợp lệ!', 'error')
                return redirect(url_for('material.materials_page'))
                
            material_id = request.form.get('material_id')
            
            expense = Expense.query.filter_by(date_time=date_time, material_id=material_id).first()
            if expense:
                db.session.delete(expense)
                db.session.commit()
                flash('Xóa đơn nhập hàng thành công!', 'success')
            else:
                flash('Không tìm thấy đơn nhập hàng!', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'Lỗi khi xóa đơn nhập hàng: {str(e)}', 'error')
    
    return redirect(url_for('material.materials_page'))
    
