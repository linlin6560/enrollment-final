from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional  # 添加 Optional 导入
from flask_ckeditor import CKEditorField  # 添加这行导入CKEditorField

class PostForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired(), Length(min=1, max=120)])
    category = SelectField('分类（可选）', coerce=int, validators=[Optional()], default=0)
    content = CKEditorField('内容', validators=[DataRequired()])
    summary = TextAreaField('摘要', validators=[Length(0, 300)])
    # 添加图片上传字段
    image = FileField('封面图片', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], '只允许上传图片文件!')
    ])
    submit = SubmitField('发布')