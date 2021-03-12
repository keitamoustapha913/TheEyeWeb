#!/usr/bin/env python3





import os
from pathlib import Path

import time

import uuid

import cv2  # pip install opencv-python
import numpy as np  # pip install numpy

from PIL import Image as PIL_Image  # pip install Pillow

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
            '''
            print(
                f'Try {tries+1} of {tries_max}: waiting for {sleep_time_secs} '
                f'secs for a device to be connected!')
            '''
            for sec_count in range(sleep_time_secs):
                time.sleep(1)
                '''
                print(f'{sec_count + 1 } seconds passed ',
                      '.' * sec_count, end='\r')
                '''
            tries += 1
        else:
            #print(f'Created {len(devices)} Polar device(s)')
            return devices
    else:
        raise Exception(f'No device found! Please connect a device and run '
                        f'the example again.') 






def capture_polar(device, pixel_format_name = 'PolarizeMono8' ,directory = '.', img_id = f'{uuid.uuid1()}'):

    # Get nodes ---------------------------------------------------------------
    nodes = device.nodemap.get_node(['Width', 'Height', 'PixelFormat',
                                     'GainAuto','Gain', 'ExposureTime',
                                     'ExposureAuto', 'AcquisitionFrameRateEnable',
                                     'AcquisitionFrameRate'])

    nodes['GainAuto'].value = 'Off' # Continuous
    nodes['Gain'].value = 14.0                                

    nodes['ExposureAuto'].value = 'Off'  # Continuous
    nodes['ExposureTime'].value = 47178.0  # [33.456, 199818.384]

    n_fps = 5.0
    nodes['AcquisitionFrameRateEnable'].value = True
    nodes['AcquisitionFrameRate'].value = n_fps


    #print(f'number of nodes collected : {len(nodes)}')
    # Nodes
    #print('Setting Width to its maximum value')
    nodes['Width'].value = nodes['Width'].max

    #print('Setting Height to its maximum value')
    height = nodes['Height']
    height.value = height.max

    # Set pixel format to PolarizeMono8 
    pixel_format_name = pixel_format_name
    #print(f'Setting Pixel Format to {pixel_format_name}')
    nodes['PixelFormat'].value = pixel_format_name

    # Grab and save an image buffer -------------------------------------------
    #print('Starting stream')
    with device.start_stream(5):
      
        #print('Grabbing an image buffer')
        # Grabbing Polar
        buffer_is_incomplete = True
        while buffer_is_incomplete:
            #print('Grabbing an image buffer')
            # Optional args
            image_buffer = device.get_buffer()
            if image_buffer.is_incomplete:
                print('ERROR: buffer.is_incomplete.')
                device.requeue_buffer(image_buffer)
            else:
                buffer_is_incomplete = False


        """
        print(f' Width X Height = ' 
              f'{image_buffer.width} x {image_buffer.height}')
        """

        #print(f" image_buffer.bits_per_pixel = { image_buffer.bits_per_pixel} " )
        
        #img_id = uuid.uuid1()

        # To save an image Pillow needs an array that is shaped to
        # (height, width). In order to obtain such an array we use numpy
        # library
        #print('Converting image buffer to a numpy array')

        # Buffer.pdata is a (uint8, ctypes.c_ubyte)
        # Buffer.data is a list of elements each represents one byte. Therefore
        # for Mono8 each element represents a pixel.

        #
        # Method 1 (from Buffer.data)
        #
        # dtype is uint8 because Buffer.data returns a list or bytes and pixel
        # format is also Mono8.
        # NOTE:
        # if 'ChunkModeActive' node value is True then the Buffer.data is
        # a list of (image data + the chunkdata) so data list needs to be
        # truncated to have image data only.
        # can use either :
        #  - device.nodemap['ChunkModeActive'].value   (expensive)
        #  - buffer.has_chunkdata                 (less expensive)
        image_only_data = None
        bytes_pre_pixel = int(image_buffer.bits_per_pixel / 8)
        if image_buffer.has_chunkdata:
            # 8 is the number of bits in a byte
            
            image_size_in_bytes = image_buffer.height * \
                image_buffer.width * bytes_pre_pixel

            image_only_data = image_buffer.data[:image_size_in_bytes]
        else:
            image_only_data = image_buffer.data

        #print(f" len image {pixel_format_name} : { len(image_only_data) } ") 
        #print(f"image_only_data[0:9] : {image_only_data[0:9]}")
        nparray = np.asarray(image_only_data, dtype=np.uint8)
        #print(f"nparray[0:9] : {nparray[0:9]}")
        # Reshape array for pillow

        if bytes_pre_pixel != 1 :
            nparray_reshaped = nparray.reshape( (image_buffer.height,
                                                image_buffer.width,
                                                bytes_pre_pixel) )

            for i in range(nparray_reshaped.shape[2]):
                img = nparray_reshaped[:,:,i]

                #jpg_name = f'from_{pixel_format_name}_channel_{i}_{img_id}_to_png_with_pil.jpg'
                #img_pil = PIL_Image.fromarray(img)
                #img_pil.save(jpg_name)

                png_name = f'{directory}/from_{pixel_format_name}_channel_{i}_{img_id}_to_png_with_pil.png'
                img_pil = PIL_Image.fromarray(img)
                img_pil.save(png_name)
        else :
            nparray_reshaped = nparray.reshape( (image_buffer.height, 
                                                image_buffer.width) )
            png_name = f'{directory}/from_{pixel_format_name}_no_channel__{img_id}_to_png_with_pil.png'
            img_pil = PIL_Image.fromarray(nparray_reshaped)
            img_pil.save(png_name)
                                              
        
        # Save image
        #print('Saving image')
        
        #npy_name = f'from_{pixel_format_name}_{img_id}_to_png_with_pil.npy'
        #png_name = f'from_{pixel_format_name}_{img_id}_to_png_with_pil.png'
        
        #np.save(npy_name, nparray_reshaped)
	
        png_full__name = f'{directory}/from_{pixel_format_name}_full_{img_id}_to_png_with_pil.png'
        png_array = PIL_Image.fromarray(nparray_reshaped)
        png_array.save(png_full__name)
        
        """
        print(f'Saved image path is: {Path(os.getcwd()) / png_name}')
         
        # RAW
        t1 = time.time()
        png_raw_name = f'{directory}/from_{pixel_format_name}_raw_to_png_with_opencv_{img_id}.png'
        
        cv2.imwrite(png_raw_name, nparray_reshaped)
        t2 = time.time()
        print(f'\n \nsaving  images in seconds: {t2 -t1 }')
        print(f'Saved image path is: {Path(os.getcwd())/png_raw_name}')
        """

        device.requeue_buffer(image_buffer)

        image_name = os.path.basename(png_name)

        return image_name
