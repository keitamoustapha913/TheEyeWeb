#!/usr/bin/env python3

from flask import Flask,url_for #, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_server.config import Config
import string
import random
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import helpers as admin_helpers
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

import uuid
import os

import pandas as pd 
from datetime import datetime

from flask_cors import CORS




# Flask login 
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'admin.login_view'
login_manager.login_message_category = 'info'



# Instance database
db = SQLAlchemy()

from flask_server.home_index.auth_model import User
from flask_server.dashboard_views.expert_dashboard.exp_model import ExpertModel
from flask_server.dashboard_views.camera_dashboard.cam_model import CameraModel
from flask_server.dashboard_views.trash_dashboard.trash_model import TrashModel
from flask_server.dashboard_views.training_dashboard.train_model import TrainModel
from flask_server.dashboard_views.prediction_dashboard.pred_model import PredModel


# Create Flask application
app = Flask(__name__)
app.config.from_object(Config)


CORS(app)

# Create Flask database 
db.init_app(app)



# Create flask Login
bcrypt.init_app(app)
login_manager.init_app(app)
# Create user loader function
@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)



# Admin interface Model Views

from flask_server.home_index.views import MyModelView
from flask_server.dashboard_views.expert_dashboard import MyExpertDashboard
from flask_server.dashboard_views.camera_dashboard import MyCameraDashboard
from flask_server.dashboard_views.trash_dashboard import MyTrashDashboard
from flask_server.dashboard_views.training_dashboard import MyTrainingDashboard
from flask_server.dashboard_views.prediction_dashboard import MyPredictionDashboard


from flask_server.home_index import MyAdminIndexView

admin = Admin(app, name='TheEye', \
                   index_view=MyAdminIndexView(name="Home",url="/") , \
                   base_template='admin/custom/custom_base_ext.html', 
                   template_mode='bootstrap3', 

                   )


admin.add_view(MyModelView(User, db.session))

# Camera_Dashboard
admin.add_view(MyCameraDashboard(model = CameraModel,
                                 session = db.session ,
                                 name='Camera Dashboard', 
                                 endpoint= 'camera_dashboard', 

                                 ) 
                                )


# Expert Dashboard 
admin.add_view(MyExpertDashboard( model = ExpertModel, 
                                  session = db.session , 
                                  name='Expert Dashboard', 
                                  endpoint= 'expert_dashboard') 
                                  )

# Trash Dashboard
admin.add_view(MyTrashDashboard( model = TrashModel, 
                                 session = db.session , 
                                 name='Trash Dashboard',  
                                 endpoint= 'trash_dashboard')
                                 )

# Training Dashboard
admin.add_view(MyTrainingDashboard( model = TrainModel, 
                                    session = db.session , 
                                    name='Training Dashboard',  
                                    endpoint= 'training_dashboard'))

# Prediction Dashboard
admin.add_view(MyPredictionDashboard( model = PredModel, 
                                      session = db.session , 
                                      name='Prediction Dashboard',  
                                      endpoint= 'prediction_dashboard'))


"""
# Favicon 
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon/favicon.ico', mimetype='image/vnd.microsoft.icon')
#
"""
"""#Blueprints registrations
from flask_server.Home_blueprint.routes import Home_bp
app.register_blueprint(Home_bp)

from flask_server.User_blueprint.routes import User_bp
app.register_blueprint(User_bp)"""



def create_app(config_class=Config):

    # random database creation
    with app.app_context():
        
        #db.create_all()
        """
        
        db.drop_all()
        db.create_all()

       
        test_user = User(login="test", email="test@test.com" , password=bcrypt.generate_password_hash("test"))
        db.session.add(test_user)


        db.session.commit()
        # /home/devinsider/Documents/Projects/SymmeEye/Application/Eye_App/TheEyeWeb/flask_server/static/Data/csv/Init_firebase_extraction/Init_csv_to_server/init_flask_csv_labeled_82c766d6-72c8-11eb-95b7-00155ddf6e13.csv
        df = pd.read_csv(  os.path.join( os.environ.get('SYMME_EYE_DATA_CSV_DIR') , "Init_firebase_extraction", "Init_csv_to_server", "init_flask_csv_full_82c766d6-72c8-11eb-95b7-00155ddf6e13.csv" ), sep=',')
        
        print(df.head())
        for i in df.index:
            label = df.at[i,'Labels']
            if (label is None) or (label ==''):
                avgrating = label
            else: 
                avgrating =  label 

            filename = df.at[i,'Filename']   #Filename,FileLinks,Labels
            qpred = df.at[i,'qpred']
            #ImgFolder = df.at[i,'ImgFolder'] 
            current_full_store_path =  df.at[i,'current_full_store_path']
            prev_full_store_path =  df.at[i,'prev_full_store_path']
            full_thumbnails_store_path =  df.at[i,'full_thumbnails_store_path']
            img_id =  df.at[i,'img_id']
            #full_store_path = f"Data/Images/Init_firebase_extraction/Init_Images_Download/{ImgFolder}/{path}"

            ExpertModel_db = ExpertModel(id = uuid.uuid1(), 
                                         avgrating = avgrating, 
                                         filename=filename, 
                                         qpred = qpred, 
                                         current_full_store_path = current_full_store_path , 
                                         prev_full_store_path = prev_full_store_path, 
                                         full_thumbnails_store_path = full_thumbnails_store_path )
            db.session.add(ExpertModel_db)
        
        db.session.commit()
        """


    return app
