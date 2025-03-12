from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, SubmitField, HiddenField
from wtforms.validators import DataRequired

class UserRoleForm(FlaskForm):
    user_id = HiddenField('用户ID')
    roles = SelectMultipleField('角色', coerce=int, validators=[DataRequired()])
    submit = SubmitField('保存')