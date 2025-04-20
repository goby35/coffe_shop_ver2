from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from .models import Table, User, db
from flask_login import login_required, current_user
from functools import wraps
from flask import abort
import logging

logging.basicConfig(level=logging.DEBUG)

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.is_admin:
            return f(*args, **kwargs)
        else:
            abort(403)
    return wrap

table = Blueprint('table', __name__)

@table.route('/tables', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_tables():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            try:
                quantity = int(request.form.get('quantity'))
                if quantity < 1:
                    flash('Số lượng bàn phải lớn hơn 0', category='error')
                    return redirect(url_for('table.manage_tables'))

                # Tìm tên bàn lớn nhất hiện tại
                existing_tables = Table.query.order_by(Table.name.desc()).all()
                max_number = 0
                for t in existing_tables:
                    try:
                        num = int(t.name)
                        max_number = max(max_number, num)
                    except ValueError:
                        continue

                # Tạo các bàn mới
                for i in range(1, quantity + 1):
                    new_number = max_number + i
                    new_name = f"{new_number:02d}"  # Định dạng 01, 02, ...
                    new_table = Table(name=new_name, )  # Mặc định Còn trống
                    db.session.add(new_table)
                
                db.session.commit()
                flash(f'Đã tạo {quantity} bàn thành công', category='success')
            except ValueError:
                flash('Số lượng bàn không hợp lệ', category='error')
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error creating tables: {str(e)}")
                flash(f'Lỗi khi tạo bàn: {str(e)}', category='error')

        elif action == 'edit':
            table_id = request.form.get('id')
            table = Table.query.get(table_id)
            if table:
                try:
                    new_name = request.form.get('name')
                    if not new_name:
                        flash('Tên bàn không được để trống', category='error')
                        return jsonify({'success': False, 'error': 'Tên bàn không được để trống'})
                    table.name = new_name
                    db.session.commit()
                    flash('Cập nhật bàn thành công', category='success')
                    return jsonify({'success': True})
                except Exception as e:
                    db.session.rollback()
                    logging.error(f"Error updating table {table_id}: {str(e)}")
                    flash(f'Lỗi khi cập nhật bàn: {str(e)}', category='error')
                    return jsonify({'success': False, 'error': str(e)})
            else:
                flash('Không tìm thấy bàn', category='error')
                return jsonify({'success': False, 'error': 'Không tìm thấy bàn'})

        elif action == 'delete_multiple':
            try:
                delete_quantity = int(request.form.get('delete_quantity'))
                if delete_quantity < 1:
                    flash('Số lượng bàn muốn xóa phải lớn hơn 0', category='error')
                    return redirect(url_for('table.manage_tables'))

                # Lấy danh sách bàn, sắp xếp theo tên giảm dần
                tables = Table.query.order_by(Table.name.desc()).all()
                if len(tables) < delete_quantity:
                    flash(f'Không đủ bàn để xóa. Hiện chỉ có {len(tables)} bàn', category='error')
                    return redirect(url_for('table.manage_tables'))

                # Xóa từ bàn có tên lớn nhất
                for table in tables[:delete_quantity]:
                    db.session.delete(table)
                
                db.session.commit()
                flash(f'Đã xóa {delete_quantity} bàn thành công', category='success')
            except ValueError:
                flash('Số lượng bàn không hợp lệ', category='error')
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error deleting tables: {str(e)}")
                flash(f'Lỗi khi xóa bàn: {str(e)}', category='error')

        return redirect(url_for('table.manage_tables'))
    
    tables = Table.query.all()
    return render_template('table.html', tables=tables, user=current_user)