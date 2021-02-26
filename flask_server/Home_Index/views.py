from flask_server import  db ,bcrypt

from flask_admin import AdminIndexView, BaseView
from flask_admin import form as admin_form
from flask_admin.contrib.sqla import ModelView
from flask import Flask, url_for, redirect, render_template, request, abort, make_response, jsonify
from flask.views import MethodView
import flask_login as login
from flask_admin import helpers, expose, expose_plugview
from werkzeug.security import generate_password_hash, check_password_hash

from flask_server.Home_Index.auth_forms import LoginForm, RegistrationForm
import os
import os.path as op
from sqlalchemy.event import listens_for
from jinja2 import Markup

import logging
import sys
import glob






# create logger with 'RF_grid_serach_hyper_parameter'
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# create file handler which logs even debug messages
fh = logging.FileHandler('TheEye_web_admin.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
log.addHandler(fh)

# create console handler with a higher log level
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
log.addHandler(ch)

# Create directory for file fields to use
file_path = op.join(op.dirname(__file__), 'files')
log.debug(f'file_path:{file_path}')

try:
    os.mkdir(file_path)
except OSError as e:
    #log.error("Exception occurred", exc_info=True)
    #log.exception(f"Exception occurred{e}")
    pass
    


"""
img_name = ''
#/home/keitahp/Documents/symme_hp/phase_up/TheEye_flask/TheEye_Web/flask_server/Admin_blueprint/views.py
#/home/keitahp/Documents/symme_hp/phase_up/TheEye_flask/TheEye_Web/flask_server/static/admin/files/history_img/test
image_storage_path = op.join(op.dirname(__file__+ "/../"), 'static/admin/files/history_img/test')
#print(f'image_storage_path : {image_storage_path}')
log.debug(f'image_storage_path : {image_storage_path}')
for img_path in glob.glob('/home/keitahp/Documents/symme_hp/phase_up/TheEye_flask/TheEye_Web/flask_server/static/admin/files/history_img/test/*'):
    log.debug(f'img_path : {img_path}')
    label = int(img_path.split('_avR_')[1].split('.jpg')[0])
    img_name_strip = img_path.split('history_img/')[1].split('_avR_')[0]
    log.debug(f'img_name_strip : {img_name_strip}')
    log.debug(f'label : {label}')
    break


"""


# Create customized model view class
class MyModelView(ModelView):
    def is_accessible(self):
        return (login.current_user.is_active and
                login.current_user.is_authenticated
        )

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if login.current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('admin.login_view', next=request.url))



class ImageView(ModelView):

    create_modal = True

    def is_accessible(self):
        return (login.current_user.is_active and
                login.current_user.is_authenticated
        )

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if login.current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('admin.login_view', next=request.url))


    def _list_thumbnail(view, context, model, name):
        if not model.path:
            return ''
  
        return Markup('<img src="%s">' % url_for('static',
                                                 filename= admin_form.thumbgen_filename(model.path)))

    column_formatters = {
        'path': _list_thumbnail
    }

    # Alternative way to contribute field is to override it completely.
    # In this case, Flask-Admin won't attempt to merge various parameters for the field.
    form_extra_fields = {
        'path': admin_form.ImageUploadField('Image',
                                      base_path=file_path,
                                      thumbnail_size=(100, 100, True))
    }
