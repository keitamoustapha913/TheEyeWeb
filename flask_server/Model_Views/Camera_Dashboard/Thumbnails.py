from PIL import Image 
import os
import cv2
import uuid

from flask_admin.form import thumbgen_filename


# https://note.nkmk.me/en/python-opencv-hconcat-vconcat-np-tile/
def hconcat_resize_min(im_list, interpolation=cv2.INTER_CUBIC):
    h_min = min(im.shape[0] for im in im_list)
    im_list_resize = [cv2.resize(im, (int(im.shape[1] * h_min / im.shape[0]), h_min), interpolation=interpolation)
                      for im in im_list]
    return cv2.hconcat(im_list_resize)

#im_h_resize = hconcat_resize_min([im1, im2, im1])

def copy_images(imgs_names_list = [] , current_directory = '.', new_directory = '', thumb_name ='', thumb_directory=''):
    imgs_list = []
    for img_name in imgs_names_list:
        if img_name != thumb_name:
            image = cv2.imread( os.path.join(current_directory, f'{img_name}' ), cv2.IMREAD_UNCHANGED)
            cv2.imwrite(os.path.join(new_directory, f'{img_name}' ) , image)

        else:
            image = cv2.imread(os.path.join(current_directory, f'{img_name}' ), cv2.IMREAD_UNCHANGED)
            #thumb_directory =  os.path.join( os.path.dirname( os.path.dirname(new_directory) ) ,  f"thumbnails")
            thumb_directory = os.path.join(os.environ.get('SYMME_EYE_APPLICATION_DIR'), thumb_directory )
            if not os.path.exists( thumb_directory):
                os.makedirs(thumb_directory)
            cv2.imwrite(os.path.join(thumb_directory, f'{img_name}', ) , image)
        os.remove( os.path.join(current_directory, f'{img_name}' ))



def thumb_gen( imgs_names_list = [] , thumb_directory = '',current_directory = '',  img_id = f'{uuid.uuid1()}'):


    #directory = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'), 'Camera_Capture', f'{directory}')
    imgs_list = []
    for img_name in imgs_names_list:
        # creating a object  
        image = cv2.imread(os.path.join(current_directory, f'{img_name}' ), cv2.IMREAD_UNCHANGED)

        dim = (320, 45)
        # perform the actual resizing of the image and show it
        resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
        imgs_list.append(resized)

    img_h_resize = hconcat_resize_min( imgs_list )
    thumb_name = thumbgen_filename(  f"{img_id}.jpg" )

    cv2.imwrite(os.path.join(thumb_directory, thumb_name ) , img_h_resize)

    return thumb_name