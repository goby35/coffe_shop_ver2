from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    password = db.Column(db.String(200), nullable=False)
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'is_admin': self.is_admin
        }

class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    orders = db.relationship('Order', backref='table', lazy=True)

    def to_dict(self):
        # Tìm đơn hàng chưa hoàn thành
        active_order = Order.query.filter_by(table_id=self.id)\
            .join(OrderStatus)\
            .filter(OrderStatus.finish_time.is_(None))\
            .first()
        return {
            'id': self.id,
            'name': self.name,
            'status': active_order is None,  # True nếu trống, False nếu đã đặt
            'orderId': active_order.id if active_order else None  # Trả về order_id nếu có
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_time = db.Column(db.DateTime, nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.relationship('OrderStatus', backref='order', uselist=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'order_time': self.order_time.isoformat(),
            'table_id': self.table_id,
            'user_id': self.user_id,
            'total_amount': self.total_amount,
            'status': self.status.to_dict() if self.status else None,
            'items': [item.to_dict() for item in self.items]
        }

class OrderStatus(db.Model):
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    finish_time = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'order_id': self.order_id,
            'finish_time': self.finish_time.isoformat() if self.finish_time else None
        }

class OrderItem(db.Model):
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
    count = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'order_id': self.order_id,
            'item_id': self.item_id,
            'count': self.count,
            'item': self.item.to_dict()
        }

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    items = db.relationship('Item', backref='category', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name
        }

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    order_items = db.relationship('OrderItem', backref='item', lazy=True)
    prices = db.relationship('PriceItem', backref='item', lazy=True)
    image_url = db.Column(db.String(255), default='default-menu.png')

    def to_dict(self):
        latest_price = PriceItem.query.filter_by(item_id=self.id)\
            .order_by(PriceItem.updated_date.desc())\
            .first()
        return {
            'id': self.id,
            'name': self.name,
            'category_id': self.category_id,
            'price': self.get_latest_price(),
            'image_url': self.image_url
        }
    def get_latest_price(self):
        latest_price = PriceItem.query.filter_by(item_id=self.id)\
            .order_by(PriceItem.updated_date.desc())\
            .first()
        return latest_price.price if latest_price else 0

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    expenses = db.relationship('Expense', backref='material', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'unit': self.unit
        }

class Expense(db.Model):
    date_time = db.Column(db.DateTime, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), primary_key=True)
    count = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'date_time': self.date_time.isoformat(),
            'material_id': self.material_id,
            'count': self.count,
            'price': self.price
        }

class PriceItem(db.Model):
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), primary_key=True)
    updated_date = db.Column(db.DateTime, primary_key=True)
    price = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            'item_id': self.item_id,
            'updated_date': self.updated_date.isoformat(),
            'price': self.price
        }


