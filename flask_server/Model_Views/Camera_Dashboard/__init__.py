from flask import redirect,flash,make_response, url_for, request, jsonify, abort,render_template, send_from_directory

from flask_admin import BaseView
from flask.views import MethodView
from flask_admin import helpers, expose, expose_plugview
from flask_login import current_user
import os


import os
import time
from pathlib import Path
import uuid
import cv2  # pip install opencv-python
import numpy as np  # pip install numpy

from arena_api.system import system




def create_devices_with_tries():
    """
    This function waits for the user to connect a device before raising
    an exception
    """

    tries = 0
    tries_max = 6
    sleep_time_secs = 10
    while tries < tries_max:  # Wait for device for 60 seconds
        devices = system.create_device()
        if not devices:
            print(
                f'Try {tries+1} of {tries_max}: waiting for {sleep_time_secs} '
                f'secs for a device to be connected!')
            for sec_count in range(sleep_time_secs):
                time.sleep(1)
                print(f'{sec_count + 1 } seconds passed ',
                      '.' * sec_count, end='\r')
            tries += 1
        else:
            print(f'Created {len(devices)} Polar device(s)')
            return devices
    else:
        raise Exception(f'No device found! Please connect a device and run '
                        f'the example again.') 



def create_thermal():
    # Create device Thermal
    cam_therm = cv2.VideoCapture(0)
    if not cam_therm.isOpened():
        print('\n\nWARNING: Thermal Cam is not Opened')
        exit()
    print(f" \n\t Thermal Devices Created : /dev/Video0 usb-FLIR_Boson_63516-video-index0 ")
    return cam_therm


def capture_therm(cam_therm, directory = '.',img_id = f'{uuid.uuid1()}'):

    t1 = time.time()
    ret_therm, frame_therm = cam_therm.read()

    if ret_therm:
        # RAW
        png_raw_name = f'{directory}/from_thermal_raw_to_png_with_opencv_{img_id}.png'
        cv2.imwrite(png_raw_name, frame_therm)
        t2 = time.time()
        print(f'\n \nsaving  images in seconds: {t2 -t1 }')
        print(f'Saved image path is: {Path(os.getcwd())/png_raw_name}')
        
        

        # colormap
        t1 = time.time()
        frame_therm = cv2.flip(frame_therm, -1)  # rotate 180°
        frame_therm = cv2.applyColorMap(frame_therm, cv2.COLORMAP_HOT) 
        png_colormap_name = f'{directory}/from_thermal_colormap_Hot_to_png_with_opencv_{img_id}.png'
        cv2.imwrite(png_colormap_name, frame_therm)
        t2 = time.time()
        print(f'\n \nsaving  images in seconds: {t2 -t1 }')
        print(f'Saved image path is: {Path(os.getcwd())/png_colormap_name}')
        
    else:
        print('\n\nWARNING: ret_therm is None')
        exit()



def capture_polar(device, pixel_format_name = 'PolarizedAolp_BayerRG8' ,directory = '.', img_id = f'{uuid.uuid1()}'):

    # Get nodes ---------------------------------------------------------------
    nodes = device.nodemap.get_node(['Width', 'Height', 'PixelFormat'])

    print(f'number of nodes collected : {len(nodes)}')
    # Nodes
    print('Setting Width to its maximum value')
    nodes['Width'].value = nodes['Width'].max

    print('Setting Height to its maximum value')
    height = nodes['Height']
    height.value = height.max

    # Set pixel format to PolarizedDolp_Mono8
    pixel_format_name = pixel_format_name
    print(f'Setting Pixel Format to {pixel_format_name}')
    nodes['PixelFormat'].value = pixel_format_name

    # Grab and save an image buffer -------------------------------------------
    print('Starting stream')
    t1 = time.time()
    with device.start_stream(1):
      
        print('Grabbing an image buffer')
        # Grabbing Polar
        image_buffer = device.get_buffer()  # Optional args

        print(f' Width X Height = '
              f'{image_buffer.width} x {image_buffer.height}')

        # np.ctypeslib.as_array() detects that Buffer.pdata is (uint8, c_ubyte)
        # type so it interprets each byte as an element.
        # For 16Bit images Buffer.pdata must be cast to (uint16, c_ushort)
        # using ctypes.cast(). After casting, np.ctypeslib.as_array() can
        # interpret every two bytes as one array element (a pixel).
        print('Converting image buffer to a numpy array')
        nparray_reshaped = np.ctypeslib.as_array(image_buffer.pdata,
                                                 (image_buffer.height,
                                                  image_buffer.width))
        t2 = time.time()
        print(f'\n \nloading images : {t2 -t1 }')
        # Saving --------------------------------------------------------------
        print('Saving image')
         
        # RAW
        t1 = time.time()
        png_raw_name = f'{directory}/from_{pixel_format_name}_raw_to_png_with_opencv_{img_id}.png'
        cv2.imwrite(png_raw_name, nparray_reshaped)
        t2 = time.time()
        print(f'\n \nsaving  images in seconds: {t2 -t1 }')
        print(f'Saved image path is: {Path(os.getcwd())/png_raw_name}')

        # HSV
        t1 = time.time()
        png_hsv_name = f'{directory}/from_{pixel_format_name}_raw_hsv_to_png_with_opencv_{img_id}.png'
        cm_nparray = cv2.applyColorMap(nparray_reshaped, cv2.COLORMAP_HSV)
        cv2.imwrite(png_hsv_name, cm_nparray)
        t2 = time.time()
        print(f'\n \nsaving  images in seconds : {t2 -t1 }')
        print(f'Saved image path is: {Path(os.getcwd())/png_hsv_name}')

        device.requeue_buffer(image_buffer)


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
    
    @expose('/upload/<filename>', methods=( "GET", "POST",))
    def send_image(self, filename):
        return send_from_directory(os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" ), filename)

    @expose('/upload/', methods=("POST",))
    def upload(self): #/home/devinsider/Documents/Projects/SymmeEye/Application/Eye_App/TheEyeWeb/flask_server/static/Data/Images/Camera_Capture
        target = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" )
        print(target)
        if not os.path.isdir(target):
            os.makedirs(target)
        else:
            print("Couldn't create upload directory: {}".format(target))
        print(request.files.getlist("file"))
        for upload in request.files.getlist("file"):
            print(upload)
            print("{} is the file name".format(upload.filename))
            filename = upload.filename
            destination = "/".join([target, filename])
            print ("Accept incoming file:", filename)
            print ("Save it to:", destination)
            upload.save(destination)

        # return send_from_directory("images", filename, as_attachment=True)
        return self.render("admin/Camera_Dashboard/complete.html", image_name=filename)

    @expose('/gallery/', methods=('GET', 'POST'))
    def get_gallery(self,): 
        image_names = os.listdir(os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'), "Camera_Capture/" ))
        print(image_names)
        return self.render("admin/Camera_Dashboard/gallery.html", image_names=image_names)

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
        directory = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'), 'Camera_Capture')
        #directory = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'), 'Camera_Capture', f'{img_id}')

        try:
            os.mkdir(directory)
        except OSError as oserror:
            print(oserror)
            

        print(f"\n\n Devices used in the example: ")
        # open Thermal 
        cam_therm = create_thermal()

        # Create a device Polar
        devices = create_devices_with_tries()
        device = devices[0]
        print(f"\n\t Polar : {device} ")


        capture_therm(cam_therm, directory = directory , img_id = img_id)

        capture_polar(device = device , pixel_format_name = "PolarizedAngles_0d_45d_90d_135d_BayerRG8" ,directory = directory, img_id = img_id )
        print('\nExample finished successfully')

        return self.render("admin/Camera_Dashboard/complete.html")

