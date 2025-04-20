from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from .models import Order

views = Blueprint('views', __name__)

# Trang chủ (template Flask)
@views.route('/')
@login_required
def home():
    return render_template("base.html", user=current_user)

 