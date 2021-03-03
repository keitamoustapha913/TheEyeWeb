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



class ExpertModel(db.Model):

    id = db.Column(UUIDType(binary=False), default=uuid.uuid1(), primary_key=True)
    preview = db.Column(db.Unicode(128))
    label = db.Column(db.Unicode(64))
    
    avgrating = db.Column(ChoiceType(RatingChoices, impl=db.Integer()), nullable=True)
    qpred = db.Column(db.Unicode(128))

    filename = db.Column(db.Unicode(128) )

    prev_full_store_path = db.Column(db.Unicode(128))
    current_full_store_path = db.Column(db.Unicode(128))
    full_thumbnails_store_path = db.Column(db.Unicode(128))

    prev_dashboard = db.Column(db.Unicode(32))
    current_dashboard = db.Column(db.Unicode(32))

    machine_part_name = db.Column(db.Unicode(64))

    created_at = db.Column(db.DateTime(), default=datetime.now())    
    restored_at = db.Column(db.DateTime())
    
    
    def __unicode__(self):
        return self.name

