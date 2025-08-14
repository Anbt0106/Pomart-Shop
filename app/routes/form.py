from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (StringField, TextAreaField, DecimalField, IntegerField,
                     BooleanField, DateField, SubmitField, MultipleFileField,
                     SelectField)
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class ShopItemForm(FlaskForm):
    """
    Form for adding or editing a shop item, reflecting the Product model.
    """
    name = StringField('Tên sản phẩm', validators=[DataRequired(), Length(min=2, max=200)])
    description = TextAreaField('Mô tả', validators=[Optional()])
    price = DecimalField('Giá', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Số lượng', validators=[DataRequired(), NumberRange(min=0)])
    is_active = BooleanField('Hoạt động', default=True)
    is_featured = BooleanField('Nổi bật', default=False)
    date_released = DateField('Ngày mở bán', format='%Y-%m-%d', validators=[Optional()])

    collection = StringField('Bộ sưu tập', validators=[Optional(), Length(max=100)])

    image = MultipleFileField('Hình ảnh sản phẩm', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Chỉ chấp nhận file ảnh!')
    ])

    submit = SubmitField('Save')

