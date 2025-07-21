# Database Migration Guide

## Tổng quan
Dự án Popmart Demo đã được cập nhật với thiết kế database mới, bao gồm đầy đủ các tính năng e-commerce.

## Các thay đổi chính

### 1. Models đã được cập nhật:
- **User & UserAddress**: Quản lý người dùng và địa chỉ
- **Product & Collection**: Sản phẩm và bộ sưu tập
- **Order & OrderItem**: Đơn hàng và chi tiết đơn hàng
- **Cart**: Giỏ hàng
- **Wishlist**: Danh sách yêu thích
- **Review**: Đánh giá sản phẩm
- **Notification**: Thông báo
- **Discount**: Mã giảm giá
- **PaymentTransaction**: Giao dịch thanh toán
- **ProductImage**: Hình ảnh sản phẩm
- **InventoryLog**: Lịch sử tồn kho

### 2. Cấu trúc file:
```
app/models/
├── user.py          # User, UserAddress
├── product.py       # Product, Collection, ProductImage, InventoryLog, Wishlist
└── order.py         # Order, OrderItem, Cart, PaymentTransaction, Discount, Review, Notification
```

## Cách triển khai

### Bước 1: Backup database cũ (nếu cần)
```bash
# Nếu dùng PostgreSQL
pg_dump popmart_demo > backup_old.sql

# Nếu dùng SQLite
cp instance/popmart_demo.db instance/popmart_demo_backup.db
```

### Bước 2: Tạo database mới
```bash
# Chạy script tạo database
python create_database.py
```

### Bước 3: Kiểm tra kết nối
```bash
# Chạy ứng dụng
python main.py
```

## Cấu trúc Database mới

### Bảng Users
- Quản lý thông tin người dùng
- Hỗ trợ admin và user thường
- Tích hợp với Flask-Login

### Bảng Products
- Thông tin sản phẩm Popmart
- Hỗ trợ nhiều hình ảnh
- Quản lý tồn kho
- Phân loại theo collections

### Bảng Orders
- Quản lý đơn hàng hoàn chỉnh
- Trạng thái đơn hàng và thanh toán
- Hỗ trợ mã giảm giá
- Lưu trữ địa chỉ giao hàng

### Bảng Cart & Wishlist
- Giỏ hàng tạm thời
- Danh sách yêu thích
- Tích hợp với UI hiện tại

## API Endpoints cần cập nhật

### Cart Routes
```python
@app.route('/cart')
@app.route('/cart/add/<int:product_id>')
@app.route('/cart/remove/<int:item_id>')
@app.route('/cart/update/<int:item_id>')
```

### Wishlist Routes
```python
@app.route('/favorite')
@app.route('/favorite/add/<int:product_id>')
@app.route('/favorite/remove/<int:product_id>')
```

### Order Routes
```python
@app.route('/checkout')
@app.route('/orders')
@app.route('/orders/<int:order_id>')
```

### Review Routes
```python
@app.route('/product/<int:product_id>/review')
@app.route('/reviews')
```

## Sample Data

Script `create_database.py` sẽ tạo:
- 1 admin user (admin/admin123)
- 1 regular user (johndoe/password123)
- 3 collections (Dimoo, Pucky, Skullpanda)
- 3 products với hình ảnh
- 1 sample order
- 1 sample review
- 1 sample notification

## Lưu ý quan trọng

1. **Migration**: Database cũ sẽ bị xóa hoàn toàn
2. **Images**: Cần cập nhật đường dẫn hình ảnh trong static/img/
3. **Routes**: Cần cập nhật các route để sử dụng models mới
4. **Templates**: Có thể cần cập nhật templates để hiển thị dữ liệu mới

## Troubleshooting

### Lỗi Import
```bash
pip install -r requirements.txt
```

### Lỗi Database Connection
Kiểm tra cấu hình trong `app/__init__.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:01062004@localhost:5432/popmart_demo'
```

### Lỗi Model Import
Đảm bảo tất cả models được import trong `app/__init__.py`

## Next Steps

1. Cập nhật các route để sử dụng models mới
2. Tạo templates cho cart, wishlist, orders
3. Thêm chức năng thanh toán
4. Tích hợp với payment gateway
5. Thêm chức năng admin panel 