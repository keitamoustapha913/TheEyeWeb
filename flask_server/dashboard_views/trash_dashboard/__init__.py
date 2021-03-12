from flask import (redirect,flash,make_response, 
                   url_for, request, jsonify, 
                   abort,render_template, 
                   send_from_directory , send_file)

from flask.views import MethodView
from flask_admin import helpers, expose, expose_plugview
from flask_login import current_user

import glob

import os
import time
from datetime import datetime
from pathlib import Path
import uuid

from ..camera_dashboard.utils import DirectoryZip
from .utils import trash_delete

from jinja2 import Markup
from flask_admin import form as admin_form


from flask_admin.actions import action
from flask_admin.babel import gettext, ngettext, lazy_gettext
from flask_admin.contrib.sqla import ModelView


from flask_server import db
from .trash_model import TrashModel
from ..camera_dashboard.cam_model import CameraModel
from ..expert_dashboard.exp_model import ExpertModel
from flask_admin.model.template import TemplateLinkRowAction
from flask_admin.helpers import (get_form_data, validate_form_on_submit,
                                 get_redirect_target, flash_errors)

from flask_admin.contrib.sqla import tools

#from flask_admin.contrib.sqla.filters import  DateBetweenFilter


import requests




class MyTrashDashboard(ModelView):


    
    file_path = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" )

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
        'created_at': 'Creation Date',
        'trashed_at': 'Trashed Date'
    }

    " List of column to show in the table"
    column_display_pk = True
    column_list = ( 'id', 'preview' , 'avgrating', 'qpred', 'label', 'filename', 'created_at','trashed_at', )
    #column_exclude_list = ('full_store_path')

    # Added default sort by created date
    column_default_sort = ('trashed_at', True)

    
    """Searchable columns """
    column_searchable_list = ( 'label', 'filename' )

    column_filters =['avgrating',
                     'qpred', 
                     
                     'created_at',
                     'trashed_at',
                     ]

   
    can_create = False
    can_edit = False
    can_delete = False
    
    # Modals
    details_modal = True
    """Setting this to true will display the details_view as a modal dialog."""

    # Pagination 
    can_set_page_size  = True # Edit number of items which can be ( 20 / 50 / 100 ) per page 

    # To view preview image
    can_view_details = True
    column_details_list = [ 'preview','avgrating','qpred', 'label','filename' ,'created_at','trashed_at' ]
    
    # 

    # addding an extra row Action 
    """
    column_extra_row_actions = [    # Add a new action button
                    #EndpointLinkRowAction(icon_class = 'fa fa-refresh', endpoint= '.my_action_f', title="Train it", ),
                    # For downloading the row image
                    TemplateLinkRowAction("row_actions.download_row", "Download this image set"),
                ]
    """

                

    
    def _preview_thumbnail(view, context, model, name):
        if not model.full_thumbnails_store_path:
            return ''
        #static/Data/Images/Camera_Capture
        return Markup('<img src="%s" style="width: 30vw;" class="img-thumbnail" >' % url_for('static',
                                                 filename= f"{model.full_thumbnails_store_path}"))

    column_formatters = {
        'preview': _preview_thumbnail
    }

    @action('restore',
            lazy_gettext('Restore'),
            lazy_gettext('Are you sure you want to restore selected records?'))
    def action_restore(self, ids):
        try:            
            query = tools.get_query_for_ids(self.get_query(), self.model, ids)

            if self.fast_mass_delete:
                count = query.delete(synchronize_session=False)
            else:
                count = 0

                dashboards_dict = {
                                    'camera': CameraModel ,
                                    'expert': ExpertModel,
                                    'trash' : TrashModel, 
                                  }

                for m in query.all():
                     
                    print(f"\n\n m.prev_dashboard : {m.prev_dashboard}\n\n")
                    
                    restored_model_db = dashboards_dict[m.prev_dashboard]( id = m.id, 
                                                full_thumbnails_store_path = m.full_thumbnails_store_path, 
                                                label = m.label,
                                                avgrating = m.avgrating,
                                                qpred = m.qpred,
                                                prev_full_store_path = m.prev_full_store_path,
                                                current_full_store_path = m.current_full_store_path,
                                                filename = m.filename ,  
                                                prev_dashboard = m.current_dashboard,
                                                current_dashboard = m.prev_dashboard,
                                                created_at = m.created_at,
                                                restored_at = datetime.now(),
                                                )

                    self.session.add(restored_model_db)                    
                    if self.delete_model(m):
                        count += 1
                self.session.commit()

            flash(ngettext('Record was successfully restored .',
                           '%(count)s records were successfully restored.',
                           count,
                           count=count), 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

            flash(gettext('Failed to restore the records. %(error)s', error=str(ex)), 'error')

    @action('remove',
            lazy_gettext('Delete'),
            lazy_gettext('Are you sure you want to delete selected records?'))
    def action_remove(self, ids):
        try:
            query = tools.get_query_for_ids(self.get_query(), self.model, ids)

            if self.fast_mass_delete:
                count = query.delete(synchronize_session=False)
            else:
                count = 0

                for m in query.all():
                    imgs_main_dir = os.path.join( os.environ.get('SYMME_EYE_APPLICATION_DIR'), m.current_full_store_path ) 
                    img_thumb_path = os.path.join( os.environ.get('SYMME_EYE_APPLICATION_DIR'),m.full_thumbnails_store_path) 
                    trash_delete(imgs_main_dir = imgs_main_dir, img_thumb_path = img_thumb_path )

                    if self.delete_model(m):
                        count += 1

            self.session.commit()

            flash(ngettext('Record was successfully deleted.',
                           '%(count)s records were successfully deleted.',
                           count,
                           count=count), 'success')
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

            flash(gettext('Failed to delete records. %(error)s', error=str(ex)), 'error')
    

    def on_model_delete(self, model):
        #imgs_main_dir = model.current_full_store_path
        #img_thumb_path =os.path.join( os.environ.get('SYMME_EYE_APPLICATION_DIR'),model.full_thumbnails_store_path) 
        #trash_delete(imgs_main_dir = imgs_main_dir, img_thumb_path = img_thumb_path )
        pass


    @expose('/')
    def index_view(self):
   
        return super(MyTrashDashboard, self).index_view()

    
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
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('admin.login_view', next=request.url))
    

