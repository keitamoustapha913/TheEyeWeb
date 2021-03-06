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
from ..trash_dashboard.utils import trash_delete
from .utils import ( dataset_maker, parse_images_dirs,
                     labeled_dirs_maker_from_csv, copy_images_to_label_from_csv  )

from jinja2 import Markup
from flask_admin import form as admin_form


from flask_admin.actions import action
from flask_admin.babel import gettext, ngettext, lazy_gettext
from flask_admin.contrib.sqla import ModelView


from flask_server import db

from ..trash_dashboard.trash_model import TrashModel
from ..camera_dashboard.cam_model import CameraModel
from ..expert_dashboard.exp_model import ExpertModel
from .train_model import TrainModel

from flask_admin.model.template import TemplateLinkRowAction
from flask_admin.helpers import (get_form_data, validate_form_on_submit,
                                 get_redirect_target, flash_errors)

from flask_admin.contrib.sqla import tools

#from flask_admin.contrib.sqla.filters import  DateBetweenFilter

#from .compile_fit_train import compile_fit


import requests




class MyTrainingDashboard(ModelView):
    
    # Main Directory Creation for training
    ml_model_path = os.path.join(os.environ.get('SYMME_EYE_DATA_DIR'),"ml_models" )
    if not os.path.exists(ml_model_path):
        os.makedirs(ml_model_path)

    ml_training_path = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"deep_learning_images" , "training_images"  )
    if not os.path.exists(ml_training_path):
        os.makedirs(ml_training_path)

    ml_testing_path = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'), "deep_learning_images", "testing_images"  )
    if not os.path.exists(ml_testing_path):
        os.makedirs(ml_testing_path)

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
        'to_train_at': 'Sent to training Date'
    }

    " List of column to show in the table"
    column_display_pk = True
    column_list = ( 'id', 'preview' , 'avgrating', 'qpred', 'label', 'filename','trained_at', )
    #column_exclude_list = ('full_store_path')

    # Added default sort by sent to trainig date
    column_default_sort = ('to_train_at', True)

    list_template = 'admin/training_dashboard/list.html' 
    """Default list view template"""

    """Searchable columns """
    column_searchable_list = ( 'label', 'filename' )

    column_filters =['avgrating',
                     'qpred', 
                     
                     'created_at',
                     'to_train_at',
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
   
        return super(MyTrainingDashboard, self).index_view()

    
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



    @expose('/start_training/', methods=("POST",))
    def start_training(self):
        print('\n TRAINING STARTING ...!\n\n')
        
        t1 = time.time()
        img_id = uuid.uuid1()

        models = self.session.query(TrainModel).all()

        dataset_csv_path_list = dataset_maker(models = models, 
                                              to_csv_path = self.ml_training_path , 
                                              is_training = True)

        labeled_dirs_maker_from_csv(dirs_path_list = dataset_csv_path_list)

        copy_images_to_label_from_csv(dataset_csv_path_list = dataset_csv_path_list)

        #compile_fit( data_dir = self.ml_training_path, batch_size = 2 , img_height = 180 , img_width = 180)

        flash(f" training #{img_id} was successfully started", category='success')

        return jsonify({'result':'success'})
    

