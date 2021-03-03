from flask import (redirect,flash,make_response, 
                   url_for, request, jsonify, 
                   abort,render_template, 
                   send_from_directory , send_file)

from flask_admin import BaseView
from flask.views import MethodView
from flask_admin import helpers, expose, expose_plugview
from flask_login import current_user
import os
import glob

from jinja2 import Markup
from flask_admin import form as admin_form


from flask_admin.actions import action
from flask_admin.babel import gettext, ngettext, lazy_gettext

from flask_admin.contrib.sqla import ModelView

from datetime import datetime
import time

from .camera_dashboard.utils import DirectoryZip


from flask_server import db
from .trash_dashboard.trash_model import TrashModel

from flask_admin.model.template import TemplateLinkRowAction
from flask_admin.helpers import (get_form_data, validate_form_on_submit,
                                 get_redirect_target, flash_errors)

from flask_admin.contrib.sqla import tools

import requests



class MyBaseDashboard(ModelView):

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
    }

    " List of column to show in the table"
    column_display_pk = True
    column_list = (  'preview' , 'avgrating', 'qpred', 'label', 'filename', 'created_at','trashed_at', )
    #column_exclude_list = ('full_store_path')

    # Added default sort by created date
    column_default_sort = ('created_at', True)

    

    """Searchable columns """
    column_searchable_list = ( 'label', 'filename' )

    column_editable_list = (  'avgrating','label',)

    column_filters =['avgrating',
                     'qpred', 
                     'created_at',
                     ]

    
    # Forms
    form_columns = ( 'filename', 'label', 'avgrating','qpred',  )

    form_widget_args = {
        'filename': {
            'readonly': True,
        },
        'qpred': {
            'readonly': True
        },
        
    }
    
    # Export to csv
    can_export = True
    export_types = ['csv']
    column_export_list = ['id', 'filename', 'label','avgrating','qpred','current_full_store_path' , 'full_thumbnails_store_path' ]
    export_max_rows = 10000
   
    can_create = True
    can_edit = True
    can_delete = True

    
    # Modals
    edit_modal = True
    """Setting this to true will display the edit_view as a modal dialog."""

    create_modal = True
    """Setting this to true will display the create_view as a modal dialog."""

    details_modal = True
    """Setting this to true will display the details_view as a modal dialog."""

    # Pagination 
    can_set_page_size  = True # Edit number of items which can be ( 20 / 50 / 100 ) per page 

    # To view preview image
    can_view_details = True
    column_details_list = [ 'preview','avgrating','qpred', 'label','filename' ,'created_at' ]
    


    # addding an extra row Action 
    
    column_extra_row_actions = [    # Add a new action button
                                #EndpointLinkRowAction(icon_class = 'fa fa-refresh', endpoint= '.my_action_f', title="Train it", ),
                                # For downloading the row image
                                TemplateLinkRowAction("row_actions.download_row", "Download this image set"),
                                            
                                ]
    
    
    def after_model_change(self,form, model, is_created):
        
        if is_created:
            img_id = uuid.uuid1()

            #print(f"\n\n model before : {model.id} img_id : {img_id}")
            current_directory = os.path.join( self.file_path, f"temp")
            model.id = img_id
            model.prev_full_store_path =  os.path.join( current_directory, f"{model.filename}") 

            thumb_name = admin_form.thumbgen_filename(  f"{model.filename}" )
            thumb_directory = 'Data/Images/thumbnails' 
            model.full_thumbnails_store_path = os.path.join( thumb_directory,thumb_name  ) 
            
            imgs_names_list = os.listdir(current_directory)
            model.current_full_store_path = os.path.join( new_directory ,f"{model.filename}"  )

            new_directory = os.path.join(self.file_path , f"{model.id}")
            if not os.path.exists( new_directory):
                os.makedirs(new_directory)

            copy_images(imgs_names_list = imgs_names_list , current_directory = current_directory, 
                        new_directory = new_directory, thumb_name = thumb_name,thumb_directory=thumb_directory)

            try:
                self.session.commit()
            except Exception as ex:
                self.session.rollback()

    def on_model_delete(self, model):

        trash_model_db = TrashModel( id = model.id, 
                            full_thumbnails_store_path = model.full_thumbnails_store_path, 
                            label = model.label,
                            avgrating = model.avgrating,
                            qpred = model.qpred,
                            prev_full_store_path = model.prev_full_store_path,
                            current_full_store_path = model.current_full_store_path,
                            filename = model.filename ,
                            trashed_at = datetime.now(),  
                            created_at = model.created_at)
        self.session.add(trash_model_db)
        self.session.commit()


    def _preview_thumbnail(view, context, model, name):
        if not model.full_thumbnails_store_path:
            return ''
        #static/Data/Images/Camera_Capture
        return Markup('<img src="%s" style="width: 30vw;" class="img-thumbnail" >' % url_for('static',
                                                 filename= f"{model.full_thumbnails_store_path}"))

    column_formatters = {
        'preview': _preview_thumbnail
    }

    form_extra_fields = {
        'filename': admin_form.ImageUploadField( label = 'Image Upload Here',
                                      base_path=os.path.join( file_path, f"temp"),
                                      thumbnail_size=(320, 180, True))
    }


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
