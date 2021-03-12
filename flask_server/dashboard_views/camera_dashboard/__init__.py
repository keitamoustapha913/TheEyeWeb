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

import time
from pathlib import Path
import uuid
import cv2  # pip install opencv-python
import numpy as np  # pip install numpy

from jinja2 import Markup
from flask_admin import form as admin_form


from .polar_camera import create_devices_with_tries, capture_polar
from .thermal_camera import create_thermal, capture_therm
from .utils import DirectoryZip, thumb_gen, copy_images
from ..training_dashboard.utils import copy_images_from_list


from flask_admin.actions import action
from flask_admin.babel import gettext, ngettext, lazy_gettext


from flask_admin.contrib.sqla import ModelView
from datetime import datetime

#from flask_server import db

from flask_admin.model.template import TemplateLinkRowAction
from flask_admin.helpers import (get_form_data, validate_form_on_submit,
                                 get_redirect_target, flash_errors)


from .cam_model import CameraModel
from ..trash_dashboard.trash_model import TrashModel
from ..training_dashboard.train_model import TrainModel
from ..expert_dashboard.exp_model import ExpertModel
from ..prediction_dashboard.pred_model import PredModel

#from flask_admin.contrib.sqla.filters import  DateBetweenFilter
from flask_admin.contrib.sqla import tools

import requests

#from flask_server.dashboard_views import MyBaseDashboard

file_path = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" )



class MyCameraDashboard(ModelView):

    file_path = file_path

    # Table's Columns
    column_descriptions = dict(
        preview="Preview of the Part's image",
        avgrating=' Quality Rating of the expert on the part , To be either "1=OK" or "0=KO"',
        qpred='Quality Prediction of the trained model for the Image either "OK" or "KO" ',
        label='Factory label of the part given by the Expert',
        filename='filename of the part in the storage drive',
        machine_part_name='identification of the type of part used',

    )

    column_labels = {
        'avgrating': 'Quality Rating',
        'qpred': 'Quality Predicted',
        'label': 'Factory Part Label',
        'filename': 'Storage Filename',
        'created_at': 'Creation Date',
        'machine_part_name' : 'Part type ID',
      
    }

    " List of column to show in the table"
    column_display_pk = True
    column_list = ( 'id' , 'preview' , 'avgrating', 'qpred', 'label', 'machine_part_name', 'created_at', )
    #column_exclude_list = ('full_store_path')

    # Added default sort by created date
    column_default_sort = ('created_at', True)


    """Searchable columns """
    column_searchable_list = ( 'label', 'id','machine_part_name', )

    column_editable_list = (  'avgrating','label',)

    column_filters =['avgrating',
                     'qpred', 
                     'machine_part_name',
                     'created_at',
                     ]

    # Forms
    form_columns = ( 'filename', 'label', 'avgrating','qpred','machine_part_name',  )

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
    column_export_list = ['id', 'filename', 'label','avgrating','qpred','machine_part_name','current_full_store_path' , 'full_thumbnails_store_path' ,'created_at']
    export_max_rows = 10000
    # Index view html template
    # templates/
    list_template = 'admin/camera_dashboard/list.html'

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
    column_details_list = [ 'preview','avgrating','qpred', 'label','machine_part_name','filename' ,'created_at' ]
    


    # addding an extra row Action 
    
    column_extra_row_actions = [    # Add a new action button
                    #EndpointLinkRowAction(icon_class = 'fa fa-refresh', endpoint= '.my_action_f', title="Train it", ),
                    # For downloading the row image
                    TemplateLinkRowAction("row_actions.download_row", "Download this image set"),
                    TemplateLinkRowAction("row_actions.save_to_expert_row", "Save this record !"),

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
                    print(f"\n\n m.id : {m.id}\n\n")
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


    @action('prediction', 'Prediction', 'Are you sure you want to predict the quality of selected records?')
    def action_prediction(self, ids):
        try:
            print(f"\n\n ids : {ids}\n\n")

            query = CameraModel.query.filter(CameraModel.id.in_(ids))
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
                                            machine_part_name = m.machine_part_name,
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

            query = CameraModel.query.filter(CameraModel.id.in_(ids))
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
                                            current_full_store_path = m.current_full_store_path,
                                            prev_dashboard = m.current_dashboard , 
                                            current_dashboard = 'train',
                                            filename = m.filename ,
                                            to_train_at = datetime.now(),  
                                            created_at = m.created_at)

                self.session.add(train_model_db)
                
                print(f"\n\n Sending to training : \
                       m.id : {m.id} \
                       m.full_thumbnails_store_path {m.full_thumbnails_store_path}\n") 

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

        #dictToSend = {'training':'True'}
        #res = requests.post( f"http://localhost:5111"+ self.get_url('.get_gallery'), json=dictToSend)


    @action('save', 'Save', 'Are you sure you want to save selected records?')
    def action_save(self, ids):
        try:
            print(f"\n\n Saving to History the following records:\n\tids : {ids}\n\n")

            query = CameraModel.query.filter(CameraModel.id.in_(ids))
            #return_url = get_redirect_target() or self.get_url('.index_view')
            return_url = get_redirect_target() or self.get_url('admin.login_view')
            
            count = 0
            
            #self.history_path =  os.path.join( os.environ.get('SYMME_EYE_APPLICATION_DIR'),'Data', 'Images', 'history' )

            for m in query.all():
                current_directory = os.path.join( os.environ.get('SYMME_EYE_APPLICATION_DIR'), f"{m.current_full_store_path}" )
                images_paths_list = glob.glob( f"{current_directory}/*" )  

                from_static_img_history_directory =  os.path.join( 'Data', 'Images', 'history', f'{m.id}')
                new_dir = os.path.join( os.environ.get('SYMME_EYE_APPLICATION_DIR'), from_static_img_history_directory )
                copy_images_from_list(images_paths_list = images_paths_list, new_directory = new_dir )
                
                
                expert_model_db = ExpertModel( id = m.id, 
                                            full_thumbnails_store_path = m.full_thumbnails_store_path, 
                                            label = m.label,
                                            avgrating = m.avgrating,
                                            qpred = m.qpred,
                                            prev_full_store_path = m.current_full_store_path,
                                            current_full_store_path = from_static_img_history_directory,
                                            prev_dashboard = m.current_dashboard , 
                                            current_dashboard = 'expert',
                                            filename = m.filename ,
                                            saved_at = datetime.now(),  
                                            created_at = m.created_at)

                self.session.add(expert_model_db)
                
                print(f"\n\n Sending to history : \
                       id : {m.id} \
                       current_full_store_path {from_static_img_history_directory}\n\
                       prev_full_store_path {m.current_full_store_path}\n\n") 

                self.session.flush()
                self.session.delete(m)
                
                count += 1
        
            self.session.commit()
            flash(ngettext('the record was successfully saved to expert dashboard.',
                           '%(count)s records were successfully sent to expert.',
                           count,
                           count=count))
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

            flash(gettext('Failed to send records to expert dashboard. %(error)s', error=str(ex)), 'error')



    def after_model_change(self,form, model, is_created):
        
        if is_created:
            img_id = uuid.uuid1()
            #print(f"\n\n model before : {model.id} img_id : {img_id}")
            current_directory = os.path.join( file_path, f"temp")
            model.id = img_id
            model.prev_full_store_path =  os.path.join( current_directory, f"{model.filename}") 

            thumb_name = admin_form.thumbgen_filename(  f"{model.filename}" )
            thumb_directory = 'Data/Images/thumbnails' 
            model.full_thumbnails_store_path = os.path.join( thumb_directory,thumb_name  ) 

            model.created_at = datetime.now()
            model.current_dashboard = "camera"
            quality = model.avgrating
            print(f"\n\n Quality Rating   : {quality}")



            imgs_names_list = os.listdir(current_directory)
            
            new_directory = os.path.join(file_path , f"{model.id}")
            #model.current_full_store_path = os.path.join( new_directory ,f"{model.filename}"  )
            
            if not os.path.exists( new_directory):
                os.makedirs(new_directory)

            model.current_full_store_path = new_directory

            copy_images(imgs_names_list = imgs_names_list , current_directory = current_directory, 
                        new_directory = new_directory, thumb_name = thumb_name,thumb_directory=thumb_directory)

            try:
                self.session.commit()
            except Exception as ex:
                self.session.rollback()

    
    def on_model_delete(self, model):
        print(f"\n\n\n model.prev_dashboard : {model.prev_dashboard}\
                \n\n\n model.current_dashboard : {model.current_dashboard}\
                \n\n ")


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

        
                

    
    def _preview_thumbnail(view, context, model, name):
        if not model.full_thumbnails_store_path:
            return ''
        #static/Data/Images/Camera_Capture
        return Markup('<img src="%s" style="width: 30vw;" class="img-thumbnail" >' % url_for('static',
                                                 filename= f"{model.full_thumbnails_store_path}"))

    column_formatters = {
        'preview': _preview_thumbnail
    }

    # Alternative way to contribute field is to override it completely.
    # In this case, Flask-Admin won't attempt to merge various parameters for the field.
    form_extra_fields = {
        'filename': admin_form.ImageUploadField( label = 'Image Upload Here',
                                      base_path=os.path.join( file_path, f"temp"),
                                      thumbnail_size=(320, 180, True))
    }

    

    @expose('/')
    def index_view(self):
        # Use the delete row form as a template for the download row form # 
        self._template_args['download_row_form'] = self.delete_form()
        self._template_args['save_to_expert_row_form'] = self.delete_form()
        #return self.render('admin/Camera_Dashboard/camera_dashboard.html')
        return super(MyCameraDashboard, self).index_view()

    
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
    


    """
    @expose('/upload/<directory>/<filename>', methods=( "GET", "POST",))
    def send_image(self, directory , filename):
        if directory == 'None':
            return send_from_directory(os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" ), f"{filename}")

        return send_from_directory(os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" ), f"{directory}/{filename}")

    @expose('/upload/', methods=("POST",))
    def upload(self): #/home/devinsider/Documents/Projects/SymmeEye/Application/Eye_App/TheEyeWeb/flask_server/static/Data/Images/Camera_Capture
        img_id = uuid.uuid1()
        
        target = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" , f'{img_id}')
        #print(target)

        if not os.path.exists(target):
            os.makedirs(target)

        images_names_split = []
        images_direct_split = []
        #print(request.files.getlist("file"))
        for upload in request.files.getlist("file"):
            #print(upload)
            #print("{} is the file name".format(upload.filename))
            filename = upload.filename
            destination = "/".join([target, filename])
            #print ("Accept incoming file:", filename)
            #print ("Save it to:", destination)
            upload.save(destination)
            images_direct_split.append(f'{img_id}')
            images_names_split.append(filename)

        # return send_from_directory("images", filename, as_attachment=True)
        #return self.render("admin/Camera_Dashboard/complete.html", image_name=filename)
        #return self.render('admin/Camera_Dashboard/camera_dashboard.html')
        return self.render("admin/camera_dashboard/gallery.html", directory=images_direct_split, image_names=images_names_split, zip = zip)

    @expose('/gallery/', methods=('GET', 'POST'))
    def get_gallery(self,): 
        image_names = os.listdir(os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'), "Camera_Capture" ))
        capture_dir_path = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" )
        images_glob = glob.glob(f"{capture_dir_path}/**/*",  recursive = True)
        images_names_split = []
        images_direct_split = []
        for image_glob in images_glob: 
            #print(image_glob)
            image_glob = image_glob.split(sep=f"{capture_dir_path}/")[1]
            direct_name = os.path.split(image_glob)
            #print(direct_name)
            images_direct_split.append(direct_name[0])
            images_names_split.append(direct_name[1])

        #print(images_names_split)
        return self.render("admin/camera_dashboard/gallery.html", directory=images_direct_split, image_names=images_names_split, zip = zip)

    """


    @expose('/camera_capture/', methods=( "GET", "POST",))
    def camera_capture(self):
        print('\nWARNING:\n CAMERA CAPTURE STARTING ...!')
        
        t1 = time.time()
        img_id = uuid.uuid1()
        #directory = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'), 'Camera_Capture')
        from_static_imgs_directory = os.path.join( 'Data', 'Images', 'Camera_Capture', f'{img_id}')
        from_static_thumb_directory = os.path.join( 'Data', 'Images', 'thumbnails')

        directory = os.path.join(os.environ.get('SYMME_EYE_APPLICATION_DIR'), from_static_imgs_directory)
        thumb_directory =  os.path.join(os.environ.get('SYMME_EYE_APPLICATION_DIR'), from_static_thumb_directory)  

        if not os.path.exists(directory):
            os.makedirs(directory)

        #images_direct_split = [f'{img_id}', f'{img_id}']
        
        #print(f"\n\n Devices used in the example: ")
        # open Thermal 
        cam_therm = create_thermal()
        
        
        # Create a device Polar
        devices = create_devices_with_tries()
        device = devices[0]
        #print(f"\n\t Polar : {device} ")        
        

        thermal_name = capture_therm(cam_therm = cam_therm, 
                                      directory = directory , 
                                      img_id = img_id,
                                      )

        #images_names_split.append(thermal_name)

        polar_name = capture_polar(device = device , 
                                   pixel_format_name = "PolarizedAngles_0d_45d_90d_135d_BayerRG8" ,
                                   directory = directory, img_id = img_id ,
                                   )

        #images_names_split.append(polar_name)
        print(f"\nCapture finished successfully in : {time.time() - t1 } Seconds \n \n") # Capture finished successfully in : 8.00595760345459 Seconds

        images_names_split = [thermal_name , polar_name]
        #images_names_split = [thermal_name ]
        images_names_string = ','.join(images_names_split)

        thumb_name = thumb_gen( imgs_names_list = images_names_split ,
                                thumb_directory = thumb_directory,
                                current_directory = directory, 
                                img_id = img_id,
                                 )
        
        current_full_store_path_directory = from_static_imgs_directory 
        full_thumbnails_store_path =  os.path.join(from_static_thumb_directory, f"{thumb_name}")

        CameraModel_db = CameraModel( id = img_id, 
                                      full_thumbnails_store_path = full_thumbnails_store_path, 
                                      current_full_store_path = current_full_store_path_directory,
                                      filename = images_names_string , 
                                      created_at = datetime.now() ,
                                      current_dashboard = "camera",
                                      )

        self.session.add(CameraModel_db)
        self.session.commit()
        
        flash(f"Image #{img_id} was successfully captured")
        #return self.render("admin/Camera_Dashboard/complete.html")
        #return self.render("admin/Camera_Dashboard/gallery.html", directory=[f'{img_id}'], image_names=[thumb_name], zip = zip)
        result = {'result':'success'}
        return jsonify(result)



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
            to_zip_dir = os.path.join(os.environ.get('SYMME_EYE_WEB_STATIC_DIR'), "Data/Images/downloads_zips") 
            zip_filename = DirectoryZip(dir_name = directory, to_zip_dir = to_zip_dir, id_stamp = f"{model.id}")
            zip_download_name = os.path.basename(zip_filename) 

            flash(f'Image #{id} was successfully downloaded .','success')
        else:
            flash_errors(download_row_form, message='Failed to download record. %(error)s')
        '''
        # same as send_from_directory
        return send_file(f'{zip_filename}',
            mimetype = 'zip',
            attachment_filename= f'{zip_download_name}',
            as_attachment = True) 
        '''
        return send_from_directory(to_zip_dir, f'{zip_download_name}', as_attachment = True)


    @expose('/save_to_expert/', methods=('POST',))
    def save_to_expert_row_view(self):
        print(f"\n\nSaving to expert dashboard ...\n\n\n")

        """
            save image view. Only POST method is allowed.
        """
        return_url = get_redirect_target() or self.get_url('.index_view')

        # Using the default delete form as the train_row form 
      
        save_to_expert_row_form = self.delete_form()

        if self.validate_form(save_to_expert_row_form):
            # id is InputRequired()
            img_id = save_to_expert_row_form.id.data

            model = self.get_one(img_id)
            
            if model is None:
                flash(gettext('Record does not exist.'), 'error')
                return redirect(return_url)

            print(f"\n\nThe model id is : {model.id}\n\n")
            current_directory = os.path.join( os.environ.get('SYMME_EYE_APPLICATION_DIR'), f"{model.current_full_store_path}" )
            images_paths_list = glob.glob( f"{current_directory}/*" )  

            from_static_img_history_directory =  os.path.join( 'Data', 'Images', 'history', f'{model.id}')
            new_dir = os.path.join( os.environ.get('SYMME_EYE_APPLICATION_DIR'), from_static_img_history_directory )
            copy_images_from_list(images_paths_list = images_paths_list, new_directory = new_dir )
            
            
            expert_model_db = ExpertModel( id = model.id, 
                                        full_thumbnails_store_path = model.full_thumbnails_store_path, 
                                        label = model.label,
                                        avgrating = model.avgrating,
                                        qpred = model.qpred,
                                        prev_full_store_path = model.current_full_store_path,
                                        current_full_store_path = from_static_img_history_directory,
                                        prev_dashboard = model.current_dashboard , 
                                        current_dashboard = 'expert',
                                        filename = model.filename ,
                                        saved_at = datetime.now(),  
                                        created_at = model.created_at)

            self.session.add(expert_model_db)

            print(f"\n\n Sending to history : \
                    id : {model.id} \
                    current_full_store_path {from_static_img_history_directory}\n\
                    prev_full_store_path {model.current_full_store_path}\n\n") 

            try:
                self.session.flush()
                self.session.delete(model)
                self.session.commit()
                flash(f'Image #{img_id} was successfully saved to expert dashboard.','success')
            except Exception as ex:
                if not self.handle_view_exception(ex):
                    flash(gettext('Failed to delete record. %(error)s', error=str(ex)), 'error')

                self.session.rollback()
        
        else:
            flash_errors(save_to_expert_row_form, message='Failed to save the record. %(error)s')
  
        return redirect(return_url)
        
