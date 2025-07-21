from app import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address_id = db.Column(db.Integer, db.ForeignKey('user_addresses.id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # pending, shipped, delivered, canceled
    payment_status = db.Column(db.String(50), nullable=False)  # unpaid, paid, refunded
    discount_id = db.Column(db.Integer, db.ForeignKey('discounts.id'))
    placed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    paid_at = db.Column(db.DateTime)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True)
    payment_transactions = db.relationship('PaymentTransaction', backref='order', lazy=True)

    def __repr__(self):
        return f'<Order {self.id} - {self.status}>'

    @property
    def status_display(self):
        """Get human readable status"""
        status_map = {
            'pending': 'Chờ xử lý',
            'shipped': 'Đã gửi hàng',
            'delivered': 'Đã giao hàng',
            'canceled': 'Đã hủy'
        }
        return status_map.get(self.status, self.status)

    @property
    def payment_status_display(self):
        """Get human readable payment status"""
        payment_status_map = {
            'unpaid': 'Chưa thanh toán',
            'paid': 'Đã thanh toán',
            'refunded': 'Đã hoàn tiền'
        }
        return payment_status_map.get(self.payment_status, self.payment_status)


class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<OrderItem {self.product_id} x {self.quantity}>'

    @property
    def subtotal(self):
        """Calculate subtotal for this item"""
        return float(self.price) * self.quantity


class Cart(db.Model):
    __tablename__ = 'cart'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Cart {self.user_id} - {self.product_id} x {self.quantity}>'


class PaymentTransaction(db.Model):
    __tablename__ = 'payment_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<PaymentTransaction {self.id} - {self.amount}>'


class Discount(db.Model):
    __tablename__ = 'discounts'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Numeric(10, 2), nullable=False)
    is_percentage = db.Column(db.Boolean, nullable=False)
    min_order_amount = db.Column(db.Numeric(10, 2))
    valid_from = db.Column(db.Date, nullable=False)
    valid_to = db.Column(db.Date, nullable=False)

    # Relationships
    orders = db.relationship('Order', backref='discount', lazy=True)

    def __repr__(self):
        return f'<Discount {self.code}>'

    def is_valid(self, order_amount=0):
        """Check if discount is valid for given order amount"""
        from datetime import date
        today = date.today()
        
        if today < self.valid_from or today > self.valid_to:
            return False
            
        if self.min_order_amount and order_amount < float(self.min_order_amount):
            return False
            
        return True

    def calculate_discount(self, order_amount):
        """Calculate discount amount for given order amount"""
        if not self.is_valid(order_amount):
            return 0
            
        if self.is_percentage:
            return float(order_amount) * (float(self.value) / 100)
        else:
            return float(self.value)


class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Review {self.user_id} - {self.product_id} ({self.rating}★)>'


class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<Notification {self.title}>' 