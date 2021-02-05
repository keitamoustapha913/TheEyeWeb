
from flask import  request
from flask_admin.form import BaseForm
from wtforms.fields import HiddenField
from wtforms.validators import InputRequired


class TrainRowFormClass(BaseForm):
        id = HiddenField()
        url = HiddenField()


