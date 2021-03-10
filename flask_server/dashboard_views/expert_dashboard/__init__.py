from flask import ( redirect,flash,make_response, url_for,
                    request, jsonify, abort,render_template,
                     send_from_directory)
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
import uuid

from flask_admin import form as admin_form

# Actions
from flask_admin.actions import action
from flask_admin.babel import gettext, ngettext, lazy_gettext
from flask_admin.model.template import  TemplateLinkRowAction

from flask_admin.helpers import (get_form_data, validate_form_on_submit,
                                 get_redirect_target, flash_errors)


from flask_admin.contrib.sqla import tools
from ..trash_dashboard.trash_model import TrashModel
from ..training_dashboard.train_model import TrainModel
from ..prediction_dashboard.pred_model import PredModel
from .exp_model import ExpertModel

from ..camera_dashboard.utils import copy_images, DirectoryZip

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
        'created_at': 'Creation Date',
    }

    " List of column to show in the table"
    column_display_pk = True
    column_list = ( 'preview' , 'avgrating', 'qpred', 'label', 'filename','created_at','prev_dashboard', )
    #column_exclude_list = ('current_full_store_path')

    # Added default sort by created date
    column_default_sort = ('created_at', True)


    """Searchable columns """
    column_searchable_list = ( 'label', 'filename' )

    column_editable_list = ( 'avgrating', 'label')

    column_filters = ['avgrating',
                     'qpred', 
                     'created_at',
                     ]

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

    can_create = True
    can_edit = True
    can_delete = True

    # To view preview image
    can_view_details = True
    column_details_list = [ 'preview','avgrating','qpred', 'label','filename' ,'created_at' ]
    

    # Export to csv
    can_export = True
    export_types = ['csv']
    column_export_list = ['id', 'filename', 'label','avgrating','qpred','current_full_store_path' , 'full_thumbnails_store_path' ]
    export_max_rows = 10000


    # Modals
    edit_modal = True
    """Setting this to true will display the edit_view as a modal dialog."""

    create_modal = True
    """Setting this to true will display the create_view as a modal dialog."""

    details_modal = True
    """Setting this to true will display the details_view as a modal dialog."""

    # Pagination 
    can_set_page_size  = True # Edit number of items which can be ( 20 / 50 / 100 ) per page 


    column_extra_row_actions = [    # Add a new action button
                    #EndpointLinkRowAction(icon_class = 'fa fa-refresh', endpoint= '.my_action_f', title="Train it", ),
                    # For downloading the row image
                    TemplateLinkRowAction("row_actions.download_row", "Download this image set"),
                ]
    


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


    @action('prediction', 'Prediction', 'Are you sure you want to predict the quality of selected records?')
    def action_prediction(self, ids):
        try:
            print(f"\n\n ids : {ids}\n\n")

            query = ExpertModel.query.filter(ExpertModel.id.in_(ids))
            #return_url = get_redirect_target() or self.get_url('.index_view')
            return_url = get_redirect_target() or self.get_url('admin.login_view')
            
            count = 0
            
            for m in query.all():
                
                pred_model_db = PredModel( id = m.id, 
                                            full_thumbnails_store_path = m.full_thumbnails_store_path, 
                                            label = m.label,
                                            avgrating = m.avgrating,
                                            qpred = m.qpred,
                                            prev_dashboard = m.current_dashboard,
                                            current_dashboard =  'prediction',
                                            prev_full_store_path = m.prev_full_store_path,
                                            current_full_store_path = m.current_full_store_path,
                                            filename = m.filename ,
                                            to_pred_at = datetime.now(),  
                                            created_at = m.created_at)
                self.session.add(pred_model_db)

                count += 1
            
            self.session.commit()
            flash(ngettext('The record was successfully sent for prediction.',
                           '%(count)s records were successfully sent for predictions.',
                           count,
                           count=count))
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

            flash(gettext('Failed to send records to predictions. %(error)s', error=str(ex)), 'error')



    @action('train', 'Train', 'Are you sure you want to train selected records?')
    def action_train(self, ids):
        try:
            print(f"\n\n ids : {ids}\n\n")

            query = ExpertModel.query.filter(ExpertModel.id.in_(ids))
            #return_url = get_redirect_target() or self.get_url('.index_view')
            return_url = get_redirect_target() or self.get_url('admin.login_view')
            
            count = 0
            
            for m in query.all():
                
                train_model_db = TrainModel( id = m.id, 
                                            full_thumbnails_store_path = m.full_thumbnails_store_path, 
                                            label = m.label,
                                            avgrating = m.avgrating,
                                            qpred = m.qpred,
                                            prev_full_store_path = m.prev_full_store_path,
                                            prev_dashboard = m.current_dashboard,
                                            current_dashboard =  'train',
                                            current_full_store_path = m.current_full_store_path,
                                            filename = m.filename ,
                                            to_train_at = datetime.now(),  
                                            created_at = m.created_at)
                self.session.add(train_model_db)
                """
                print(f"\n\n Sending to training : \
                       m.id : {m.id} \
                       m.full_thumbnails_store_path {m.full_thumbnails_store_path}\n") 
                """
                count += 1
            
            self.session.commit()
            flash(ngettext('the record was successfully sent to training.',
                           '%(count)s records were successfully sent to training.',
                           count,
                           count=count))
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

            flash(gettext('Failed to send records to training. %(error)s', error=str(ex)), 'error')



    def after_model_change(self,form, model, is_created):
        
        if is_created:
            img_id = uuid.uuid1()
            #os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" )
            #print(f"\n\n model before : {model.id} img_id : {img_id}")
            current_directory = os.path.join( os.environ.get('SYMME_EYE_DATA_IMAGES_DIR') , "uploads")
            model.id = img_id
            model.prev_full_store_path =  os.path.join( current_directory, f"{model.filename}") 

            thumb_name = admin_form.thumbgen_filename(  f"{model.filename}" )
            thumb_directory = 'Data/Images/thumbnails' 
            model.full_thumbnails_store_path = os.path.join( thumb_directory,thumb_name  ) 

            model.created_at = datetime.now()
            model.current_dashboard = "expert"
            quality = model.avgrating
            #print(f"\n\n Quality Rating   : {quality}")

            imgs_names_list = os.listdir(current_directory)
            
            new_directory = os.path.join(file_path , f"{model.id}")
            #model.current_full_store_path = os.path.join( new_directory ,f"{model.filename}"  )
            
            if not os.path.exists( new_directory):
                os.makedirs(new_directory)

            model.current_full_store_path = new_directory

            copy_images(imgs_names_list = imgs_names_list , 
                        current_directory = current_directory, 
                        new_directory = new_directory, 
                        thumb_name = thumb_name,
                        thumb_directory=thumb_directory)

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
                            created_at = model.created_at,
                            prev_dashboard = model.current_dashboard,
                            current_dashboard = "trash",
                            )
        self.session.add(trash_model_db)
        
                 
    

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
                                      base_path=os.path.join( os.environ.get('SYMME_EYE_DATA_IMAGES_DIR') , "uploads"),
                                      thumbnail_size=(320, 180, True))
    }



    @expose('/')
    def index_view(self):
        
        #self._template_args['train_row_form'] = self.delete_form()
        self._template_args['download_row_form'] = self.delete_form()
        return super(MyExpertDashboard, self).index_view()



    @expose('/download_image/', methods=('POST',))
    def download_row_view(self):
        """
            download image view. Only POST method is allowed.
        """
        return_url = get_redirect_target() or self.get_url('.index_view')

        # Using the default delete form as the train_row form 
      
        download_row_form = self.delete_form()

        if self.validate_form(download_row_form):
            # id is InputRequired()
            id = download_row_form.id.data

            model = self.get_one(id)
            
            if model is None:
                flash(gettext('Record does not exist.'), 'error')
                return redirect(return_url)

            # message is flashed from within train_row_model if it fails
            print(f"\n\n model path")
            
            directory = os.path.join(os.environ.get('SYMME_EYE_APPLICATION_DIR'), f"{model.current_full_store_path}")
            to_zip_dir = os.path.join(os.environ.get('SYMME_EYE_APPLICATION_DIR'), "Data/Images/downloads_zips") 
            zip_filename = DirectoryZip(dir_name = directory, to_zip_dir = to_zip_dir, id_stamp = f"{model.id}")
            zip_download_name = os.path.basename(zip_filename) 

            flash(f'Image #{id} was successfully downloaded .','success')
        else:
            flash_errors(download_row_form, message='Failed to download record. %(error)s')

        return send_from_directory(to_zip_dir, f'{zip_download_name}', as_attachment = True)




