from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, number_range

#{{ form.csrf_token() }}
#if form.validate_on_submit() and request.method == 'POST':

class ReserveForm(FlaskForm):
    room = HiddenField()
    days = IntegerField('días', validators=[DataRequired(), number_range(min=1, max=7, message="La reservación debe ser de mínimo 1 día y máximo de 7")])
    submit = SubmitField('Reservar')

