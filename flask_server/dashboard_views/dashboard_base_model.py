#!/usr/bin/env python3
#

from flask_server import db
from datetime import datetime
import uuid

from sqlalchemy_utils import ChoiceType,UUIDType
from flask_admin.babel import lazy_gettext as _


class DashboardBaseModel(db.Model):

    QualityChoices = [
            ( -99 , _(u'Empty') ),
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

    created_at = db.Column(db.DateTime(), default=datetime.now())    
    
    def __unicode__(self):
        return self.name

