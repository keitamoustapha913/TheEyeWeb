#!/usr/bin/env python3

import os
import glob

def trash_delete(imgs_main_dir = '', img_thumb_path = '' ):
    #imgs_main_dir = m.current_full_store_path
    #img_thumb_path =os.path.join( os.environ.get('SYMME_EYE_APPLICATION_DIR'),m.full_thumbnails_store_path) 
    
    if os.path.exists(imgs_main_dir):
        imgs_main_list = glob.glob( os.path.join(imgs_main_dir,'*'))
        for img in imgs_main_list:
            os.remove(img)
        os.remove(imgs_main_dir)
    #thumbnails/0b6b92a2-6027-11e9-997c-a088b4f3a790_TE_Ro19n3T3TgJHOmA77Oeh_avR_0_thumb
    #thumb/0d7c392a-7df5-11e9-87e6-a088b4f3a790_TE_Ro19n3T3TgJHOmA77Oeh_avR_0_thumb
    #Camera_Capture/0b6b92a2-6027-11e9-997c-a088b4f3a790_TE_Ro19n3T3TgJHOmA77Oeh_avR_0_thumb
    if os.path.isfile(img_thumb_path):
        #print(f"\n\n img_thumb_path : {img_thumb_path}")
        os.unlink(img_thumb_path)

    print(f"\n\n img_thumb_path : {img_thumb_path} \n\n and \n\n imgs_main_dir : {imgs_main_dir}")

    