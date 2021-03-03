from flask_server import  db ,bcrypt

from flask_admin import AdminIndexView, BaseView
from flask_admin import form as admin_form
from flask_admin.contrib.sqla import ModelView
from flask import Flask, url_for, redirect, render_template, request, abort, make_response, jsonify
from flask.views import MethodView
import flask_login as login
from flask_admin import helpers, expose, expose_plugview
from werkzeug.security import generate_password_hash, check_password_hash

from flask_server.home_index.auth_forms import LoginForm, RegistrationForm
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

if not os.path.exists(file_path) :
    os.mkdir(file_path)


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

