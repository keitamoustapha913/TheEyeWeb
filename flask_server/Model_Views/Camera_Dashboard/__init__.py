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



from .PolarCam import create_devices_with_tries, capture_polar

from .ThermalCam import create_thermal, capture_therm
from .Thumbnails import thumb_gen

from flask_admin.contrib.sqla import ModelView




class Camera_Dashboard(BaseView):

    @expose('/')
    def index_view(self):

        return self.render('admin/Camera_Dashboard/camera_dashboard.html')

    
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
        directory = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'), 'Camera_Capture', f'{img_id}')

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
        

        thermal_name = capture_therm(cam_therm, directory = directory , img_id = img_id)
        #images_names_split.append(thermal_name)

        polar_name = capture_polar(device = device , pixel_format_name = "PolarizeMono8" ,directory = directory, img_id = img_id )
        #images_names_split.append(polar_name)
        print('\nExample finished successfully')

        images_names_split = [thermal_name , polar_name]

        thumb_name = thumb_gen( imgs_names_list = images_names_split ,directory = directory, img_id = img_id)

        #return self.render("admin/Camera_Dashboard/complete.html")
        return self.render("admin/Camera_Dashboard/gallery.html", directory=[f'{img_id}'], image_names=[thumb_name], zip = zip)


