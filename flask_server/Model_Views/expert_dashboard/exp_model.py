from flask_server import db

from sqlalchemy_utils import ChoiceType
from enum import Enum



class RatingChoices(Enum):
    Zero = 0 
    One = 1
    Two = 2
    Three = 3
    Four = 4
    Five = 5



class ExpertModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    preview = db.Column(db.Unicode(128))
    label = db.Column(db.Unicode(64))
    #avgrating = db.Column(db.Integer)
    avgrating = db.Column(ChoiceType(RatingChoices, impl=db.Integer()), nullable=True)
    #taken_at = db.Column(db.DateTime())
    path = db.Column(db.Unicode(128))
    full_store_path = db.Column(db.Unicode(128))
    qpred = db.Column(db.Unicode(128))
    
    
    def __unicode__(self):
        return self.name

