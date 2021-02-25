#!/usr/bin/env python3





import os
from pathlib import Path

import time

import uuid

import cv2  # pip install opencv-python
import numpy as np  # pip install numpy




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
        #png_raw_name = f'{directory}/from_thermal_raw_to_png_with_opencv_{img_id}.png'
        #cv2.imwrite(png_raw_name, frame_therm)
        #t2 = time.time()
        #print(f'\n \nsaving  images in seconds: {t2 -t1 }')
        #print(f'Saved image path is: {Path(os.getcwd())/png_raw_name}')
    

        # colormap
        t1 = time.time()
        frame_therm = cv2.flip(frame_therm, -1)  # rotate 180°
        #frame_therm = cv2.applyColorMap(frame_therm, cv2.COLORMAP_HOT) 
        png_colormap_name = f'{directory}/from_thermal_colormap_Hot_to_png_with_opencv_{img_id}.png'
        cv2.imwrite(png_colormap_name, frame_therm)
        # grayscale 
        png_gray_name = f'{directory}/from_thermal_gray_Hot_to_png_with_opencv_{img_id}.png'
        png_gray = cv2.cvtColor(frame_therm, cv2.COLOR_BGR2GRAY ) 
        cv2.imwrite(png_gray_name, png_gray)
        #t2 = time.time()
        #print(f'\n \nsaving  images in seconds: {t2 -t1 }')
        #print(f'Saved image path is: {Path(os.getcwd())/png_colormap_name}')

        image_name = os.path.basename(png_gray_name)

        return image_name
        
    else:
        print('\n\nWARNING: ret_therm is None')
        exit()

