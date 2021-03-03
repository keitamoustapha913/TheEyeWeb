from flask import (redirect,flash,make_response, 
                   url_for, request, jsonify, 
                   abort,render_template, 
                   send_from_directory , send_file)

from flask.views import MethodView
from flask_admin import helpers, expose, expose_plugview
from flask_login import current_user

import glob

import os
import time
from datetime import datetime
from pathlib import Path
import uuid

from ..camera_dashboard.utils import DirectoryZip

from jinja2 import Markup
from flask_admin import form as admin_form


from flask_admin.actions import action
from flask_admin.babel import gettext, ngettext, lazy_gettext
from flask_admin.contrib.sqla import ModelView


from flask_server import db
from .trash_model import TrashModel

from flask_admin.model.template import TemplateLinkRowAction
from flask_admin.helpers import (get_form_data, validate_form_on_submit,
                                 get_redirect_target, flash_errors)

from flask_admin.contrib.sqla import tools

#from flask_admin.contrib.sqla.filters import  DateBetweenFilter


import requests

file_path = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" )



class MyTrashDashboard(ModelView):


    
    file_path = file_path

    # Table's Columns
    column_descriptions = dict(
        preview="Preview of the Part's image",
        avgrating=' Quality Rating of the expert on the part , To be either "1=OK" or "0=KO"',
        qpred='Quality Prediction of the trained model for the Image either "OK" or "KO" ',
        label='Factory label of the part given by the Expert',
        filename='filename of the part in the storage drive',

    )

    column_labels = {
        'avgrating': 'Quality Rating',
        'qpred': 'Quality Predicted',
        'label': 'Factory Part Label',
        'filename': 'Storage Filename',
        'created_at': 'Creation Date',
        'trashed_at': 'Trashed Date'
    }

    " List of column to show in the table"
    column_display_pk = True
    column_list = ( 'id', 'preview' , 'avgrating', 'qpred', 'label', 'filename', 'created_at','trashed_at', )
    #column_exclude_list = ('full_store_path')

    # Added default sort by created date
    column_default_sort = ('trashed_at', True)

    
    """Searchable columns """
    column_searchable_list = ( 'label', 'filename' )

    column_filters =['avgrating',
                     'qpred', 
                     
                     'created_at',
                     'trashed_at',
                     ]

   
    can_create = False
    can_edit = False
    can_delete = True
    
    # Modals
    details_modal = True
    """Setting this to true will display the details_view as a modal dialog."""

    # Pagination 
    can_set_page_size  = True # Edit number of items which can be ( 20 / 50 / 100 ) per page 

    # To view preview image
    can_view_details = True
    column_details_list = [ 'preview','avgrating','qpred', 'label','filename' ,'created_at','trashed_at' ]
    
    # 

    # addding an extra row Action 
    """
    column_extra_row_actions = [    # Add a new action button
                    #EndpointLinkRowAction(icon_class = 'fa fa-refresh', endpoint= '.my_action_f', title="Train it", ),
                    # For downloading the row image
                    TemplateLinkRowAction("row_actions.download_row", "Download this image set"),
                ]
    """

                

    
    def _preview_thumbnail(view, context, model, name):
        if not model.full_thumbnails_store_path:
            return ''
        #static/Data/Images/Camera_Capture
        return Markup('<img src="%s" style="width: 30vw;" class="img-thumbnail" >' % url_for('static',
                                                 filename= f"{model.full_thumbnails_store_path}"))

    column_formatters = {
        'preview': _preview_thumbnail
    }
    

    @expose('/')
    def index_view(self):
   
        return super(MyTrashDashboard, self).index_view()

    
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
    
    @expose('/upload/<directory>/<filename>', methods=( "GET", "POST",))
    def send_image(self, directory , filename):
        if directory == 'None':
            return send_from_directory(os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" ), f"{filename}")

        return send_from_directory(os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" ), f"{directory}/{filename}")

    @expose('/upload/', methods=("POST",))
    def upload(self): #/home/devinsider/Documents/Projects/SymmeEye/Application/Eye_App/TheEyeWeb/flask_server/static/Data/Images/Camera_Capture
        img_id = uuid.uuid1()
        
        target = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" , f'{img_id}')
        print(target)

        if not os.path.exists(target):
            os.makedirs(target)

        images_names_split = []
        images_direct_split = []
        print(request.files.getlist("file"))
        for upload in request.files.getlist("file"):
            #print(upload)
            #print("{} is the file name".format(upload.filename))
            filename = upload.filename
            destination = "/".join([target, filename])
            #print ("Accept incoming file:", filename)
            #print ("Save it to:", destination)
            upload.save(destination)
            images_direct_split.append(f'{img_id}')
            images_names_split.append(filename)

        # return send_from_directory("images", filename, as_attachment=True)
        #return self.render("admin/Camera_Dashboard/complete.html", image_name=filename)
        #return self.render('admin/Camera_Dashboard/camera_dashboard.html')
        return self.render("admin/Camera_Dashboard/gallery.html", directory=images_direct_split, image_names=images_names_split, zip = zip)

    @expose('/gallery/', methods=('GET', 'POST'))
    def get_gallery(self,): 
        image_names = os.listdir(os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'), "Camera_Capture" ))
        capture_dir_path = os.path.join(os.environ.get('SYMME_EYE_DATA_IMAGES_DIR'),"Camera_Capture" )
        images_glob = glob.glob(f"{capture_dir_path}/**/*",  recursive = True)
        images_names_split = []
        images_direct_split = []
        for image_glob in images_glob: 
            #print(image_glob)
            image_glob = image_glob.split(sep=f"{capture_dir_path}/")[1]
            direct_name = os.path.split(image_glob)
            #print(direct_name)
            images_direct_split.append(direct_name[0])
            images_names_split.append(direct_name[1])

        #print(images_names_split)
        return self.render("admin/Camera_Dashboard/gallery.html", directory=images_direct_split, image_names=images_names_split, zip = zip)

    @expose('/download_image/', methods=('POST',))
    def download_row_view(self):
        """
            download image view. Only POST method is allowed.
        """
        return_url = get_redirect_target() or self.get_url('.index_view')

        # Using the default delete form as the train_row form 
      
        download_row_form = self.delete_form()

        if self.validate_form(download_row_form):
            # id is InputRequired()
            id = download_row_form.id.data

            model = self.get_one(id)
            
            if model is None:
                flash(gettext('Record does not exist.'), 'error')
                return redirect(return_url)

            # message is flashed from within train_row_model if it fails
            print(f"\n\n model path")
            
            directory = os.path.join(os.environ.get('SYMME_EYE_APPLICATION_DIR'), f"{model.current_full_store_path}")
            to_zip_dir = os.path.join(os.environ.get('SYMME_EYE_WEB_STATIC_DIR'), "Data/Images/Downloads") 
            zip_filename = DirectoryZip(dir_name = directory, to_zip_dir = to_zip_dir, id_stamp = f"{model.id}")
            zip_download_name = os.path.basename(zip_filename) 

            flash(f'Image #{id} was successfully downloaded .','success')
            #flash(f'model path : {model.current_full_store_path} ','success')
        else:
            flash_errors(download_row_form, message='Failed to download record. %(error)s')
        '''
        # same as send_from_directory
        return send_file(f'{zip_filename}',
            mimetype = 'zip',
            attachment_filename= f'{zip_download_name}',
            as_attachment = True) 
        '''
        return send_from_directory(to_zip_dir, f'{zip_download_name}', as_attachment = True)


