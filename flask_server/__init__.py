from flask import Flask,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_server.config import Config
import string
import random
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin import helpers as admin_helpers
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
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

from flask_server.models import Role, Image
from flask_server.Home_Index.auth_model import User
from flask_server.Model_Views.expert_dashboard.exp_model import ExpertModel

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

from flask_server.Home_Index.views import MyModelView,ImageView
from flask_server.Model_Views.expert_dashboard import MyExpertDashboard
from flask_server.Model_Views.Camera_Dashboard import Camera_Dashboard

from flask_server.Home_Index import MyAdminIndexView

admin = Admin(app, name='TheEye', \
                   index_view=MyAdminIndexView(name="Home",url="/") , \
                   base_template='admin/custom/custom_base_ext.html', template_mode='bootstrap3')


admin.add_view(MyModelView(User, db.session))

# Camera_Dashboard
admin.add_view(Camera_Dashboard(name="Camera Dashboard", endpoint= 'camera_dashboard'))


# Expert Dashboard 
admin.add_view(MyExpertDashboard(model = ExpertModel, session = db.session , endpoint= 'expertmodel'))


admin.add_view(MyModelView(model = Role, session = db.session))
admin.add_view(ImageView(Image, db.session))


"""#Blueprints registrations
from flask_server.Home_blueprint.routes import Home_bp
app.register_blueprint(Home_bp)

from flask_server.User_blueprint.routes import User_bp
app.register_blueprint(User_bp)"""



def create_app(config_class=Config):

    # random database creation
    with app.app_context():

        db.drop_all()
        db.create_all()

       
        test_user = User(login="test", email="test@test.com" , password=bcrypt.generate_password_hash("test"))
        db.session.add(test_user)

        images = ["Buffalo", "Elephant", "Leopard", "Lion", "Rhino"]
        for name in images:
            image = Image()
            image.name = name
            image.path = name.lower() + ".jpg"
            db.session.add(image)

        db.session.commit()
        # /home/devinsider/Documents/Projects/SymmeEye/Application/Eye_App/TheEyeWeb/flask_server/static/Data/csv/Init_firebase_extraction/Init_csv_to_server/init_flask_csv_labeled_82c766d6-72c8-11eb-95b7-00155ddf6e13.csv
        df = pd.read_csv(  os.path.join( os.environ.get('SYMME_EYE_DATA_CSV_DIR') , "Init_firebase_extraction", "Init_csv_to_server", "init_flask_csv_full_82c766d6-72c8-11eb-95b7-00155ddf6e13.csv" ), sep=',')
        
        print(df.head())
        for i in df.index:
            avgrating = int(df.at[i,'Labels'])
            path = df.at[i,'Filename']   #Filename,FileLinks,Labels
            qpred = df.at[i,'qpred']
            ImgFolder = df.at[i,'ImgFolder']  
            full_store_path = f"Data/Images/Init_firebase_extraction/Init_Images_Download/{ImgFolder}/{path}"
            ExpertModel_db = ExpertModel(avgrating = avgrating, path=path, qpred = qpred, full_store_path = full_store_path )
            db.session.add(ExpertModel_db)
        
        db.session.commit()



    return app