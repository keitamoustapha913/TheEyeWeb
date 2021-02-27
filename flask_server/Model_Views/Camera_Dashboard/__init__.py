from flask import redirect,flash,make_response, url_for, request, jsonify, abort,render_template, send_from_directory

from flask_admin import BaseView
from flask.views import MethodView
from flask_admin import helpers, expose, expose_plugview
from flask_login import current_user
import os
import glob

import os
import time
from pathlib import Path
import uuid
import cv2  # pip install opencv-python
import numpy as np  # pip install numpy

from jinja2 import Markup
from flask_admin import form as admin_form


from .PolarCam import create_devices_with_tries, capture_polar

from .ThermalCam import create_thermal, capture_therm
from .Thumbnails import thumb_gen, copy_images
from flask_admin.actions import action
from flask_admin.babel import gettext, ngettext
from .Cam_model import CameraDashboard
from flask_admin.contrib.sqla import ModelView
from datetime import datetime

from flask_server import db
from flask_server.Model_Views.Camera_Dashboard.Cam_model import CameraDashboard

file_path = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" )



class MyCamera_Dashboard(ModelView):

    @action('approve', 'Approve', 'Are you sure you want to approve selected users?')
    def action_approve(self, ids):
        try:
            query = CameraDashboard.query.filter(CameraDashboard.id.in_(ids))

            count = 0
            for user in query.all():
                              
                count += 1

            flash(ngettext('User was successfully approved.',
                           '%(count)s users were successfully approved.',
                           count,
                           count=count))
        except Exception as ex:
            if not self.handle_view_exception(ex):
                raise

            flash(gettext('Failed to approve users. %(error)s', error=str(ex)), 'error')


    file_path = file_path

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
    column_display_pk = True
    column_list = (  'preview' , 'avgrating', 'qpred', 'label', 'filename', 'created_at', )
    #column_exclude_list = ('full_store_path')

    """Searchable columns """
    column_searchable_list = ( 'label', 'filename' )

    column_editable_list = (  'avgrating','label',)

    column_filters = ('avgrating', 'qpred')

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
    # Index view html template
    # templates/
    list_template = 'admin/Camera_Dashboard/list.html'

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
    
    def after_model_change(self,form, model, is_created):
        
        if is_created:
            #img_id = uuid.uuid1()
            #print(f"\n\n model before : {model.id} img_id : {img_id}")
            current_directory = os.path.join( file_path, f"temp")
            #model.id = img_id
            model.prev_full_store_path =  os.path.join( current_directory, f"{model.filename}") 
            model.filename = f"{model.filename}"
            thumb_name = admin_form.thumbgen_filename(  f"{model.filename}" )
            thumb_directory = 'Data/Images/thumbnails' 
            model.full_thumbnails_store_path = os.path.join( thumb_directory,thumb_name  ) 
            new_directory = os.path.join(file_path , f"{model.id}")
            
            imgs_names_list = os.listdir(current_directory)
            model.current_full_store_path = os.path.join( new_directory ,f"{model.filename}"  )
      
            if not os.path.exists( new_directory):
                os.makedirs(new_directory)

            copy_images(imgs_names_list = imgs_names_list , current_directory = current_directory, 
                        new_directory = new_directory, thumb_name = thumb_name,thumb_directory=thumb_directory)

            try:
                db.session.commit()
            except Exception as ex:
                db.session.rollback()

            
                

    
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
                                      thumbnail_size=(320, 45, True))
    }

    

    @expose('/')
    def index_view(self):

        #return self.render('admin/Camera_Dashboard/camera_dashboard.html')
        return super(MyCamera_Dashboard, self).index_view()

    
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
    
    @expose('/upload/<directory>/<filename>', methods=( "GET", "POST",))
    def send_image(self, directory , filename):
        if directory == 'None':
            return send_from_directory(os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" ), f"{filename}")

        return send_from_directory(os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" ), f"{directory}/{filename}")

    @expose('/upload/', methods=("POST",))
    def upload(self): #/home/devinsider/Documents/Projects/SymmeEye/Application/Eye_App/TheEyeWeb/flask_server/static/Data/Images/Camera_Capture
        img_id = uuid.uuid1()
        
        target = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" , f'{img_id}')
        print(target)
        try:
            os.makedirs(target)
        except OSError as oserror:
            print(oserror)

        """
        if not os.path.isdir(target):
            os.makedirs(target)
        else:
            print("Couldn't create upload directory: {}".format(target))
        """

        images_names_split = []
        images_direct_split = []
        print(request.files.getlist("file"))
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
        return self.render("admin/Camera_Dashboard/gallery.html", directory=images_direct_split, image_names=images_names_split, zip = zip)

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

        print(images_names_split)
        return self.render("admin/Camera_Dashboard/gallery.html", directory=images_direct_split, image_names=images_names_split, zip = zip)

    @expose_plugview('/_api/1')
    class API_v1(MethodView):
        def get(self, cls):
            return cls.render('test.html', request=request, name="API_v1")

        def post(self, cls):
            return cls.render('test.html', request=request, name="API_v1")

    @expose_plugview('/_api/2')
    class API_v2(MethodView):
        def get(self, cls):
            return cls.render('test.html', request=request, name="API_v2")

        def post(self, cls):
            return cls.render('test.html', request=request, name="API_v2")

    @expose('/camera_capture/', methods=( "GET", "POST",))
    def camera_capture(self):
        print('\nWARNING:\nTHIS EXAMPLE MIGHT CHANGE THE DEVICE(S) SETTINGS!')
        print('\nExample started\n')

        img_id = uuid.uuid1()
        #directory = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'), 'Camera_Capture')
        from_static_imgs_directory = os.path.join( 'Data', 'Images', 'Camera_Capture', f'{img_id}')
        from_static_thumb_directory = os.path.join( 'Data', 'Images', 'thumbnails')
        directory = os.path.join(os.environ.get('SYMME_EYE_APPLICATION_DIR'), from_static_imgs_directory)
        thumb_directory =  os.path.join(os.environ.get('SYMME_EYE_APPLICATION_DIR'), from_static_thumb_directory)  
        try:
            os.makedirs(directory)
        except OSError as oserror:
            print(oserror)
            

        
        images_direct_split = [f'{img_id}', f'{img_id}']

        print(f"\n\n Devices used in the example: ")
        # open Thermal 
        cam_therm = create_thermal()
        
        
        # Create a device Polar
        devices = create_devices_with_tries()
        device = devices[0]
        print(f"\n\t Polar : {device} ")        
        

        thermal_name = capture_therm(cam_therm, directory = directory , 
                                      img_id = img_id)
        #images_names_split.append(thermal_name)

        polar_name = capture_polar(device = device , pixel_format_name = "PolarizedAngles_0d_45d_90d_135d_BayerRG8" ,directory = directory, img_id = img_id )
        #images_names_split.append(polar_name)
        print('\nExample finished successfully')

        images_names_split = [thermal_name , polar_name]
        #images_names_split = [thermal_name ]
        images_names_string = ','.join(images_names_split)
        thumb_name = thumb_gen( imgs_names_list = images_names_split ,thumb_directory = thumb_directory,current_directory = directory, img_id = img_id)
        
        current_full_store_path_directory = from_static_imgs_directory 
        full_thumbnails_store_path =  os.path.join(from_static_thumb_directory, f"{thumb_name}")
        CameraDashboardModel_db = CameraDashboard( full_thumbnails_store_path = full_thumbnails_store_path, current_full_store_path = current_full_store_path_directory,filename = images_names_string , created_at = datetime.now())
        db.session.add(CameraDashboardModel_db)
        db.session.commit()

        flash(f"Image #{img_id} was successfully captured")
        #return self.render("admin/Camera_Dashboard/complete.html")
        #return self.render("admin/Camera_Dashboard/gallery.html", directory=[f'{img_id}'], image_names=[thumb_name], zip = zip)
        result = {'result':'success'}
        return jsonify(result)


