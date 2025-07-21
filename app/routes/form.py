from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import FileField, SelectField, DateField
from wtforms.fields.numeric import DecimalField, IntegerField
from wtforms.fields.simple import StringField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, URL, NumberRange, Optional


class ShopItemForm(FlaskForm):
    """
    Form for adding or editing a shop item.
    This form can be extended with fields as needed.
    """
    name = StringField('Tên sản phẩm', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('Mô tả', validators=[DataRequired()])
    price = DecimalField('Giá', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Tồn kho', validators=[DataRequired(), NumberRange(min=0)])
    is_active = BooleanField('Kích hoạt', default=True)
    is_featured = BooleanField('Nổi bật', default=False)
    date_released = DateField('Ngày ra mắt', validators=[Optional()])
    collection = StringField('Bộ sưu tập', validators=[Optional(), Length(max=50)])
    image = FileField('Hình ảnh', validators=[Optional(), FileAllowed(['jpg', 'png', 'jpeg'], 'Chỉ nhận ảnh!')])
    submit = SubmitField('Lưu')