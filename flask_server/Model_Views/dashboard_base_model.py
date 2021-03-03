from flask_server import db
from datetime import datetime
import uuid

from sqlalchemy_utils import ChoiceType,UUIDType
from enum import Enum


class RatingChoices(Enum):
    Zero = 0 
    One = 1
    Two = 2
    Three = 3
    Four = 4
    Five = 5





class ModelViews(db.Model):
    id = db.Column(UUIDType(binary=False), default=uuid.uuid1, primary_key=True)
    preview = db.Column(db.Unicode(128))
    label = db.Column(db.Unicode(64))
    avgrating = db.Column(ChoiceType(RatingChoices, impl=db.Integer()), nullable=True)
    qpred = db.Column(db.Unicode(128))
    filename = db.Column(db.Unicode(128), unique=True)
    prev_full_store_path = db.Column(db.Unicode(128))
    current_full_store_path = db.Column(db.Unicode(128))
    full_thumbnails_store_path = db.Column(db.Unicode(128))
    created_at = db.Column(db.DateTime(), default=datetime.now())    
    
    def __unicode__(self):
        return self.name

