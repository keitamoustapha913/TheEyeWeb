#!/usr/bin/env python3

import os
import glob

def trash_delete(imgs_main_dir = '', img_thumb_path = '', extensions = ('*.png', '*.jpg', '*.csv')  ):
    #imgs_main_dir = m.current_full_store_path
    #img_thumb_path =os.path.join( os.environ.get('SYMME_EYE_APPLICATION_DIR'),m.full_thumbnails_store_path) 
    
    if os.path.exists(imgs_main_dir):

        image_path_list = []
        for ext in extensions:
            image_path_list.extend( glob.glob( os.path.join( imgs_main_dir, f"**/{ext}" ) ) )
       
        for ext in extensions:
            image_path_list.extend( glob.glob( os.path.join( imgs_main_dir, ext ) ) )

        for img in image_path_list:
            os.unlink(img)

    empty_dirs_list = os.listdir(imgs_main_dir)
    for empty_dir in empty_dirs_list:
        os.rmdir( os.path.join(imgs_main_dir, empty_dir) )
    # os.rmdir(dir_path)

    if os.path.isfile(img_thumb_path):
        #print(f"\n\n img_thumb_path : {img_thumb_path}")
        os.unlink(img_thumb_path)

    #print(f"\n\n img_thumb_path : {img_thumb_path} \n\n and \n\n imgs_main_dir : {image_path_list}")

    
