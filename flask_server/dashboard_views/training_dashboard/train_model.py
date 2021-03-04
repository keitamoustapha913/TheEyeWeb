#!/usr/bin/env python3


from flask_server import db
from datetime import datetime
import uuid

from sqlalchemy_utils import ChoiceType,UUIDType
from flask_admin.babel import lazy_gettext as _


class TrainModel(db.Model):

    QualityChoices = [
            ( -99 , _(u'') ),
            ( 1 , _(u'One') ),
            ( 2 , _(u'Two') ),
            ( 3 , _(u'Three') ),
            ( 4 , _(u'Four') ),
            ( 5 , _(u'Five') ),
    ]

    id = db.Column(UUIDType(binary=False), default=uuid.uuid1(), primary_key=True)
    preview = db.Column(db.Unicode(128))
    label = db.Column(db.Unicode(64))

    avgrating = db.Column(ChoiceType(QualityChoices, impl=db.Integer()), nullable=True)
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
    
    to_train_at = db.Column(db.DateTime(), default=datetime.now()) 
    trained_at = db.Column(db.DateTime())


    def __unicode__(self):
        return self.name
