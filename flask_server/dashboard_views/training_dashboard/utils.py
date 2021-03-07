#!/usr/bin/env python3

import pandas as pd
import os
from glob import glob
import cv2


#######################################################################################

def dataset_maker(models = None, to_csv_path = '', is_training = True):
    """[summary]

    Args:
        models ([type], optional): [description]. Defaults to None.
        to_csv_path (str, optional): [description]. Defaults to ''.
        is_training (bool, optional): [description]. Defaults to True.

    Returns:
        [type]: [description]
    """

    if not os.path.exists(to_csv_path) and (to_csv_path != ''):
        os.makedirs(to_csv_path)

    images_dirs_list = []
    images_labels_list = []
    for m in models:
        #print(f"\n\n m.id : {m.avgrating} m.current_full_store_path : {m.current_full_store_path}")
        #print(f"\n\n m.id : {m.avgrating} m.full_thumbnails_store_path : {m.full_thumbnails_store_path}")
        if (m.avgrating is not None) or (m.avgrating != -99) or (m.avgrating !=''):
            images_labels_list.append(m.avgrating)
            images_dirs_list.append(m.current_full_store_path)

    print(f"\n\n Number of models {len(images_dirs_list)}")
    print(f"\n\n Number of models {len(images_dirs_list)}")       

    df = pd.DataFrame( {
        'images_dirs': images_dirs_list,
        'images_labels': images_labels_list,
    })

    if is_training:
        dataset = 'training'
    else:
        dataset = 'testing'

    dataset_csv_path_list = [] 
    # df[column].unique() returns a list of unique values in that particular column
    for label in df['images_labels'].unique():
        # Filter the dataframe using that column and value from the list

        dataset_csv_name = f"{dataset}_label_{label}_df.csv"
        dataset_path = os.path.join(to_csv_path, dataset_csv_name )  

        df[df['images_labels']==label].to_csv( path_or_buf = dataset_path, sep=',',  index=False)
        dataset_csv_path_list.append(dataset_path)

    return dataset_csv_path_list


################################################################################

def labeled_dirs_maker_from_csv(dirs_path_list = []):
    """[summary]

    Args:
        dirs_path_list (list, optional): [description]. Defaults to [].

    Raises:
        Exception: [description]
    """
    if len(dirs_path_list) == 0 :
        raise Exception("\n\n dirs_path_list is empty ")
    

    for dir_path in dirs_path_list:
        dir_file = os.path.split(dir_path) 

        if not os.path.exists(dir_file[0]):
            os.makedirs(dir_path)

        if dir_file[1] != '': 
            new_dir_name = dir_file[1].split('_label_')[1].split('_df.csv')[0]
            new_dir = os.path.join(dir_file[0], new_dir_name)

            if not os.path.exists(new_dir):
                os.makedirs( new_dir )

##############################################################################

def copy_images_to_label_from_csv(dataset_csv_path_list = []):
    """[summary]

    Args:
        dataset_csv_path_list (list, optional): [description]. Defaults to [].
    """
    for dataset_csv_path in dataset_csv_path_list:
        if not os.path.exists(dataset_csv_path):
            continue

        dir_file = os.path.split(dataset_csv_path)
        labeled_dir_name = dir_file[1].split('_label_')[1].split('_df.csv')[0]
        to_dir_copy = os.path.join( dir_file[0], labeled_dir_name  )

        if not os.path.exists(to_dir_copy):
            os.makedirs(to_dir_copy)
        
        df = pd.read_csv( dataset_csv_path , sep=',')

        images_dirs_list = df['images_dirs'].values

        images_paths_list =  parse_images_dirs(images_dirs_list = images_dirs_list)

        copy_images_from_list(images_paths_list = images_paths_list, new_directory = to_dir_copy )


##########################################################################

def copy_images_from_list(images_paths_list = [], new_directory = ''):
    if not os.path.exists(new_directory) and (new_directory != ''):
        os.makedirs(new_directory)
    i = 0 
    for image_path in images_paths_list:

        if  os.path.exists(image_path) and (image_path != ''):
            i = i + 1
            image_name = os.path.basename(image_path)
            #image_name = f"img_{i}.png"
            image = cv2.imread(image_path, flags=cv2.IMREAD_UNCHANGED )
            cv2.imwrite(os.path.join(new_directory, f'{image_name}' ) , image)


#########################################################################

def parse_images_dirs(images_dirs_list = []):
    """[summary]

    Args:
        images_dirs_list (list, optional): [description]. Defaults to [].

    Returns:
        [type]: [description]
    """
    images_paths_list = []
    for image_dir in images_dirs_list:
        image_path_list = parse_image_dir(image_dir = image_dir)
        images_paths_list.extend( image_path_list )

    return images_paths_list

#########################################################################

def parse_image_dir(image_dir ='' , extensions = ('*.png', '*.jpg')):
    """[summary]

    Args:
        image_dir (str, optional): [description]. Defaults to ''.
        extensions (tuple, optional): [description]. Defaults to ( '*.png', '*.jpg').

    Returns:
        [list]: [description]
    """
    image_path_list = []
    for ext in extensions:
        image_path_list.extend( glob( os.path.join(image_dir, ext)))

    return image_path_list

