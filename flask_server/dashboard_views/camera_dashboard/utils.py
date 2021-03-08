
import os
import zipfile
import uuid

from PIL import Image 
import cv2

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
            if not os.path.exists( thumb_directory) and (thumb_directory != ''):
                os.makedirs(thumb_directory)
            cv2.imwrite(os.path.join(thumb_directory, f'{img_name}', ) , image)
        os.remove( os.path.join(current_directory, f'{img_name}' ))



def thumb_gen( imgs_names_list = [] , thumb_directory = '',current_directory = '',  img_id = f'{uuid.uuid1()}'):


    #directory = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'), 'Camera_Capture', f'{directory}')
    imgs_list = []
    for img_name in imgs_names_list:
        # creating a object  
        image = cv2.imread(os.path.join(current_directory, f'{img_name}' ), cv2.IMREAD_UNCHANGED)

        dim = (320, 180)
        # perform the actual resizing of the image and show it
        resized = cv2.resize(image, dim, interpolation = cv2.INTER_AREA)
        imgs_list.append(resized)

    img_h_resize = hconcat_resize_min( imgs_list )
    thumb_name = thumbgen_filename(  f"{img_id}.jpg" )

    cv2.imwrite(os.path.join(thumb_directory, thumb_name ) , img_h_resize)

    return thumb_name


# Declare the function to return all file paths of the particular directory
def retrieve_file_paths(dirName):
    """[summary]

    Args:
        dirName ([type]): [description]

    Returns:
        [type]: [description]
    """
 
    # setup file paths variable
    filePaths = []
    
    # Read all directory, subdirectories and file lists
    for root, directories, files in os.walk(dirName):
        for filename in files:
            # Create the full filepath by using os module.
            filePath = os.path.join(root, filename)
            filePaths.append(filePath)
            
    # return all paths
    return filePaths
    
 
# Declare the main function
def DirectoryZip(dir_name = 'mydir', to_zip_dir ='', id_stamp = uuid.uuid1()):


    """[summary]

    Args:
        dir_name (str, optional): [description]. Defaults to 'mydir'.
    """
    # Assign the name of the directory to zip
    
    # Call the function to retrieve all files and folders of the assigned directory
    filePaths = retrieve_file_paths(dir_name)
    #print(f"\n\n\n fille paths : {filePaths}")
    # printing the list of all files to be zipped
    print('\n\nThe following list of files will be zipped:')
    if len(filePaths) < 3:
        for fileName in filePaths:
            print(fileName)
            #print(The following list of files will be zipped:)
    else:
        print(f'\n\nThe following list of files will be zipped: { len(filePaths) }')
        
    # writing files to a zipfile
    # /home/sapristi/Documents/Projects/SymmeEye/Application/Eye_App/TheEyeWeb/flask_server/static
    
    zip_filename = os.path.join( to_zip_dir, f'zip_{id_stamp}.zip')
    with zipfile.ZipFile( zip_filename , mode='w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        # writing each file one by one
        for file in filePaths:
            arcname = os.path.basename(file) 
            zip_file.write(filename = file , arcname=arcname )
        
    print(f"\n{zip_filename} file is created successfully!")

    return zip_filename

