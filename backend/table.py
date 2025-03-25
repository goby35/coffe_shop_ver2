from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, jsonify
from .models import Table, User
from . import db
from flask_login import login_required, current_user
from functools import wraps
from flask import abort

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
def manage_tables():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'create':
            name = request.form.get('name')
            status = request.form.get('status') == 'true'
            new_table = Table(name=name, status=status)
            db.session.add(new_table)
            db.session.commit()
            flash('Table created successfully', category='success')
        elif action == 'edit':
            table_id = request.form.get('id')
            table = Table.query.get(table_id)
            if table:
                table.name = request.form.get('name')
                table.status = request.form.get('status') == 'true'
                db.session.commit()
                flash('Table updated successfully', category='success')
            else:
                flash('Table not found', category='error')
        elif action == 'delete':
            table_id = request.form.get('id')
            table = Table.query.get(table_id)
            if table:
                db.session.delete(table)
                db.session.commit()
                flash('Table deleted successfully', category='success')
                return jsonify(success=True)
            else:
                flash('Table not found', category='error')
        return redirect(url_for('table.manage_tables'))
    
    table = Table.query.all()
    return render_template('table.html', table=table, user=current_user)