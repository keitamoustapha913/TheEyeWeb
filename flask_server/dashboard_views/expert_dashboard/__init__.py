from flask import redirect,flash,make_response, url_for, request, jsonify, abort,render_template
#from flask_server.model_views.expert_dashboard.exp_model import ExpertModel

from flask_admin.contrib.sqla import ModelView
#from flask.views import MethodView

import flask_login as login

from flask_admin import helpers, expose, expose_plugview

import os
import os.path as op
from sqlalchemy.event import listens_for
from jinja2 import Markup

from datetime import datetime

from flask_admin import form as admin_form

# Actions
from flask_admin.actions import action
from flask_admin.babel import gettext, ngettext, lazy_gettext
from flask_admin.model.template import  TemplateLinkRowAction

from flask_admin.helpers import (get_form_data, validate_form_on_submit,
                                 get_redirect_target, flash_errors)


from flask_admin.contrib.sqla import tools
from ..trash_dashboard.trash_model import TrashModel
from .exp_model import ExpertModel
import requests

# Create directory for file fields to use
file_path = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" )
if not os.path.exists(file_path):
    os.makedirs(file_path)
#log.debug(f'file_path:{file_path}')


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
        filename='filename of the part in the storage drive',

    )

    column_labels = {
        'avgrating': 'Quality Rating',
        'qpred': 'Quality Predicted',
        'label': 'Factory Part Label',
        'filename': 'Storage Filename',
      
    }

    " List of column to show in the table"
    column_list = ( 'preview' , 'avgrating', 'qpred', 'label', 'filename' )
    #column_exclude_list = ('current_full_store_path')

    """Searchable columns """
    column_searchable_list = ( 'label', 'filename' )

    column_editable_list = ( 'avgrating', 'label')

    column_filters = ('avgrating', 'qpred')

    # Forms
    form_columns = ( 'filename', 'label', 'avgrating','qpred' ,  )

    form_widget_args = {
        'filename': {
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

    # Pagination 
    can_set_page_size  = True # Edit number of items which can be ( 20 / 50 / 100 ) per page 

    @action('delete',
            lazy_gettext('Delete'),
            lazy_gettext('Are you sure you want to delete selected records?'))
    def action_delete(self, ids):
        try:
            query = tools.get_query_for_ids(self.get_query(), self.model, ids)

            if self.fast_mass_delete:
                count = query.delete(synchronize_session=False)
            else:
                count = 0

                for m in query.all():
                    """
                    trash_model_db = TrashModel( id = m.id, 
                            full_thumbnails_store_path = m.full_thumbnails_store_path, 
                            label = m.label,
                            avgrating = m.avgrating,
                            qpred = m.qpred,
                            prev_full_store_path = m.prev_full_store_path,
                            current_full_store_path = m.current_full_store_path,
                            filename = m.filename ,
                            trashed_at = datetime.now(),  
                            created_at = m.created_at)
                    self.session.add(trash_model_db)
                    """
                    if self.delete_model(m):
                        count += 1

            self.session.commit()

            flash(ngettext('Record was successfully moved to Trash.',
                           '%(count)s records were successfully trashed.',
                           count,
                           count=count), 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

            flash(gettext('Failed to trash the records. %(error)s', error=str(ex)), 'error')

    @action('approve', 'Approve', 'Are you sure you want to approve selected users?')
    def action_approve(self, ids):
        try:
            query = ExpertModel.query.filter(ExpertModel.id.in_(ids))
            #return_url = get_redirect_target() or self.get_url('.index_view')
            return_url = get_redirect_target() or self.get_url('admin.login_view')
            
            count = 0
            
            for m in query.all():
                """
                trash_model_db = TrashModel( id = m.id, 
                                            full_thumbnails_store_path = m.full_thumbnails_store_path, 
                                            label = m.label,
                                            avgrating = m.avgrating,
                                            qpred = m.qpred,
                                            prev_full_store_path = m.prev_full_store_path,
                                            current_full_store_path = m.current_full_store_path,
                                            filename = m.filename ,
                                            trashed_at = datetime.now(),  
                                            created_at = m.created_at)
                self.session.add(trash_model_db)
                print(f"\n\n Approved : \
                       m.id : {m.id} \
                       m.created_at {m.created_at} \
                       m.full_thumbnails_store_path {m.full_thumbnails_store_path}\n") 
                """
                count += 1
            
            self.session.commit()
            flash(ngettext('User was successfully approved.',
                           '%(count)s users were successfully approved.',
                           count,
                           count=count))
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

            flash(gettext('Failed to approve users. %(error)s', error=str(ex)), 'error')

        dictToSend = {'training':'True'}
        res = requests.post( f"http://localhost:5111"+ self.get_url('.get_gallery'), json=dictToSend)

    
    

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
        if not model.full_thumbnails_store_path:
            return ''
  
        return Markup('<img src="%s" style="width: 25vw;" class="img-thumbnail" >' % url_for('static',
                                                 filename= model.full_thumbnails_store_path))

    column_formatters = {
        'preview': _preview_thumbnail
    }

    # Alternative way to contribute field is to override it completely.
    # In this case, Flask-Admin won't attempt to merge various parameters for the field.
    form_extra_fields = {
        'filename': admin_form.ImageUploadField( label = 'Image Upload Here',
                                      base_path=file_path,
                                      thumbnail_size=(100, 100, True))
    }

    # addding an extra row Action 

    column_extra_row_actions = [
                    TemplateLinkRowAction(template_name= 'row_actions.train_row', title= gettext('Train The Image Record'), )
                ]
    

    @expose('/')
    def index_view(self):
        
        self._template_args['train_row_form'] = self.delete_form()

        return super(MyExpertDashboard, self).index_view()

    @expose('/my_action')
    def my_action_f(self): 
        actions, actions_confirmation = self.get_actions_list()
        print(f"\n \n \n Return a list and a dictionary of allowed actions. Actions :  { actions} \n Confirmations {actions_confirmation} \n \n \n")
        return super(MyExpertDashboard, self).index_view()


    @expose('/trainit/', methods=('POST',))
    def train_row_view(self):
        """
            trainit model view. Only POST method is allowed.
        """
        return_url = get_redirect_target() or self.get_url('.index_view')

        # Using the default delete form as the train_row form 
      
        train_row_form = self.delete_form()

        if self.validate_form(train_row_form):
            # id is InputRequired()
            id = train_row_form.id.data

            model = self.get_one(id)

            if model is None:
                flash(gettext('Record does not exist.'), 'error')
                return redirect(return_url)

            # message is flashed from within train_row_model if it fails
            
            flash(f'Image #{id} was successfully trained .','success')
            #return make_response(jsonify({"fullpath": model.full_store_path}), 200)
            
        else:
            flash_errors(train_row_form, message='Failed to delete record. %(error)s')

        return redirect(return_url)





