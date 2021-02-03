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
from flask_server.Home_Index import MyAdminIndexView

admin = Admin(app, name='TheEye', \
                   index_view=MyAdminIndexView(name="Home",url="/") , \
                   base_template='admin/custom/custom_base_ext.html', template_mode='bootstrap3')


admin.add_view(MyModelView(User, db.session))

# Expert Dashboard 
admin.add_view(MyExpertDashboard(ExpertModel,db.session))


admin.add_view(MyModelView(Role, db.session))
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

        df = pd.read_csv('/home/keitahp/Documents/symme_hp/phase_up/TheEye_flask/TheEye_Web/flask_server/static/boot/PO_April2019-hand_all_stored_name_change.csv', sep=',')
        print(df.head())
        for i in df.index:
            avgrating = int(df.at[i,'avgRating'])#/home/keitahp/Documents/symme_hp/phase_up/TheEye_flask/TheEye_Web/flask_server/static/files/history_img/test/0afe2ce4-6054-11e9-997c-a088b4f3a790_TE_Ro19n3T3TgJHOmA77Oeh_avR_5.jpg
            path = df.at[i,'stored_img_name']
            qpred = df.at[i,'qpred']
            full_store_path = 'files/history_img/'+path
            ExpertModel_db = ExpertModel(avgrating = avgrating, path=path, qpred = qpred, full_store_path = full_store_path )
            db.session.add(ExpertModel_db)
        
        db.session.commit()



    return app