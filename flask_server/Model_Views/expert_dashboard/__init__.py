from flask import redirect, url_for, request, jsonify, abort,render_template
#from flask_server.model_views.expert_dashboard.exp_model import ExpertModel

from flask_admin.contrib.sqla import ModelView
#from flask.views import MethodView

import flask_login as login

from flask_admin import helpers, expose, expose_plugview


import os
import os.path as op
from sqlalchemy.event import listens_for
from jinja2 import Markup

from flask_admin import form as admin_form

# Create directory for file fields to use
file_path = op.join(op.dirname(__file__), 'files')
file_path = '/home/keitahp/Documents/symme_hp/phase_up/TheEye_flask/TheEye_Web/flask_server/static/history/uploads'
#log.debug(f'file_path:{file_path}')

try:
    os.mkdir(file_path)
except OSError as e:
    #log.error("Exception occurred", exc_info=True)
    #log.exception(f"Exception occurred{e}")
    pass


# Create customized base view class
class MyExpertDashboard(ModelView):

    # https://flask-admin.readthedocs.io/en/latest/_modules/flask_admin/model/base/
    #can_view_details = True

    # Table's Columns
    column_descriptions = dict(
        preview="Preview of the Part's image",
        avgrating=' Quality Rating of the expert on the part , To be either "1=OK" or "0=KO"',
        qpred='Quality Prediction of the trained model for the Image either "OK" or "KO" ',
        label='Factory label of the part given by the Expert',
        path='filename of the part in the storage drive',

    )

    column_labels = {
        'avgrating': 'Quality Rating',
        'qpred': 'Quality Predicted',
        'label': 'Factory Part Label',
        'path': 'Storage Filename',
      
    }

    " List of column to show in the table"
    column_list = ( 'preview' , 'avgrating', 'qpred', 'label', 'path' )
    #column_exclude_list = ('full_store_path')

    """Searchable columns """
    column_searchable_list = ( 'label', 'path' )

    column_editable_list = ( 'avgrating', 'label')

    column_filters = ('avgrating', 'qpred')

    # Forms
    form_columns = ( 'path', 'label', 'avgrating','qpred' ,  )

    form_widget_args = {
        'path': {
            'readonly': True
        },
        'qpred': {
            'readonly': True
        },
        
    }


    # Modals
    edit_modal = True
    """Setting this to true will display the edit_view as a modal dialog."""

    create_modal = True
    """Setting this to true will display the create_view as a modal dialog."""

    details_modal = True
    """Setting this to true will display the details_view as a modal dialog."""

    
    def is_accessible(self):

        return True
        """
        return (login.current_user.is_active and
                login.current_user.is_authenticated
        )
        """
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
    

    def _preview_thumbnail(view, context, model, name):
        if not model.full_store_path:
            return ''
  
        return Markup('<img src="%s" style="width: 25vw;" class="img-thumbnail" >' % url_for('static',
                                                 filename= model.full_store_path))

    column_formatters = {
        'preview': _preview_thumbnail
    }

    # Alternative way to contribute field is to override it completely.
    # In this case, Flask-Admin won't attempt to merge various parameters for the field.
    form_extra_fields = {
        'Uploads': admin_form.ImageUploadField( label = 'Image Upload Here',
                                      base_path=file_path,
                                      thumbnail_size=(100, 100, True))
    }
