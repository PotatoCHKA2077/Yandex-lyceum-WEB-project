from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField
from wtforms import SubmitField
from wtforms.validators import DataRequired


class NotesForm(FlaskForm):
    title = StringField("Заголовок", validators=[DataRequired()])
    content = TextAreaField("Содержание")
    file = FileField("Выберете файлы для добавления (при необходимости).")
    submit = SubmitField("Применить")
