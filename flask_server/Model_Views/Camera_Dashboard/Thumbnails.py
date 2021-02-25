from PIL import Image 
import os
import cv2
import uuid


# https://note.nkmk.me/en/python-opencv-hconcat-vconcat-np-tile/
def hconcat_resize_min(im_list, interpolation=cv2.INTER_CUBIC):
    h_min = min(im.shape[0] for im in im_list)
    im_list_resize = [cv2.resize(im, (int(im.shape[1] * h_min / im.shape[0]), h_min), interpolation=interpolation)
                      for im in im_list]
    return cv2.hconcat(im_list_resize)

#im_h_resize = hconcat_resize_min([im1, im2, im1])


def thumb_gen( imgs_names_list = [] ,directory = '.', img_id = f'{uuid.uuid1()}'):


    #directory = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'), 'Camera_Capture', f'{directory}')
    imgs_list = []
    for img_name in imgs_names_list:
        # creating a object  
        image = cv2.imread(os.path.join(directory, f'{img_name}' ), cv2.IMREAD_UNCHANGED)

        dim = (100, 100)
        # perform the actual resizing of the image and show it
        resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
        imgs_list.append(resized)

    img_h_resize = hconcat_resize_min( imgs_list )
    thumb_name = f"thumbnail_{img_id}.jpg"
    cv2.imwrite(os.path.join(directory, thumb_name ) , img_h_resize)

    return thumb_name