
import os
import zipfile
import uuid



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

