from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectMultipleField, FileField, DateField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf.file import FileAllowed, MultipleFileField

class ShopItemForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=200)])
    description = TextAreaField('Description')
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    collection = StringField('Collection', validators=[Length(max=100)])  # Optional field with max length
    image = MultipleFileField('Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])  # Changed to MultipleFileField to support multiple files
    date_released = DateField('Release Date')
    is_active = BooleanField('Active', default=True)
    is_featured = BooleanField('Featured', default=False)
    submit = SubmitField('Submit')

class AddToCartForm(FlaskForm):
    quantity = IntegerField('Quantity', validators=[
        DataRequired(), 
        NumberRange(min=1, message='Quantity must be at least 1')
    ], default=1, render_kw={
        'min': 1,
        'class': 'quantity-input'
    })

class CheckoutForm(FlaskForm):
    # Chọn địa chỉ có sẵn hoặc tạo mới
    address_choice = SelectField('Chọn địa chỉ giao hàng', 
                                choices=[('new', 'Tạo địa chỉ mới')],
                                validators=[DataRequired()])
    
    # Thông tin địa chỉ mới (chỉ hiển thị khi chọn "Tạo mới")
    recipient_name = StringField('Tên người nhận', validators=[Length(min=2, max=100)])
    phone_number = StringField('Số điện thoại', validators=[Length(min=10, max=15)])
    address = TextAreaField('Địa chỉ', validators=[Length(min=10, max=500)])
    city = StringField('Thành phố', validators=[Length(min=2, max=100)])
    postal_code = StringField('Mã bưu điện', validators=[Length(min=5, max=10)])
    country = StringField('Quốc gia', validators=[Length(min=2, max=100)])
    
    # Payment method
    payment_method = SelectField('Phương thức thanh toán', 
                               choices=[('cod', 'Thanh toán khi nhận hàng (COD)'), 
                                       ('bank', 'Chuyển khoản ngân hàng'),
                                       ('momo', 'Ví MoMo'),
                                       ('zalopay', 'ZaloPay')],
                               validators=[DataRequired()])
    
    # Optional discount code
    discount_code = StringField('Mã giảm giá (nếu có)', validators=[Length(max=50)])
    
    # Terms and conditions
    accept_terms = BooleanField('Tôi đồng ý với điều khoản và điều kiện', validators=[DataRequired()])
    
    submit = SubmitField('Đặt hàng')

class PaymentForm(FlaskForm):
    payment_method = SelectField('Phương thức thanh toán', 
                               choices=[('cod', 'Thanh toán khi nhận hàng (COD)'), 
                                       ('bank', 'Chuyển khoản ngân hàng'),
                                       ('momo', 'Ví MoMo'),
                                       ('zalopay', 'ZaloPay')],
                               validators=[DataRequired()])
    
    # Bank transfer fields (shown when bank is selected)
    bank_name = StringField('Tên ngân hàng', validators=[Length(max=100)])
    account_number = StringField('Số tài khoản', validators=[Length(max=20)])
    account_name = StringField('Tên chủ tài khoản', validators=[Length(max=100)])
    
    # E-wallet fields
    wallet_number = StringField('Số ví điện tử', validators=[Length(max=20)])
    
    submit = SubmitField('Xác nhận thanh toán')
