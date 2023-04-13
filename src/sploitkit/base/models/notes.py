# -*- coding: UTF-8 -*-
from sploitkit import *
from sploitkit.base.models.organization import Organization
from sploitkit.base.models.systems import Host
from sploitkit.base.models.users import User


class Note(Model):
    content = TextField()


class OrganizationNote(BaseModel):
    organization = ForeignKeyField(Organization)
    note         = ForeignKeyField(Note)
    
    class Meta:
        primary_key = CompositeKey("organization", "note")


class NoteHost(BaseModel):
    host = ForeignKeyField(Host)
    note = ForeignKeyField(Note)
    
    class Meta:
        primary_key = CompositeKey("host", "note")


class NoteUser(BaseModel):
    user = ForeignKeyField(User)
    note = ForeignKeyField(Note)
    
    class Meta:
        primary_key = CompositeKey("user", "note")

