from __future__ import unicode_literals

import datetime
import re
from ipaddress import ip_address
from peewee import *

from .components.store import Model as PeeweeModel, ModelBase, Trigger
from .entity import Entity, MetaEntityBase


__all__ = ["BaseModel", "Model", "IPAddressField", "MACAddressField"]


class MetaModel(ModelBase, MetaEntityBase):
    """ Metaclass of a Model. """
    triggers = []
    
    def __new__(meta, name, bases, clsdict):
        subcls = ModelBase.__new__(meta, name, bases, clsdict)
        if subcls.__name__ != "Model":
            pass
            # add triggers here
            #try:
            #    trigger = "{}_updated".format(subcls._meta.table_name)
            #    subcls.add_trigger(trigger, "AFTER", "UPDATE",
            #                       "UPDATE", "SET updated=CURRENT_TIMESTAMP")
            #except AttributeError:
            #    pass
        return subcls


class BaseModel(PeeweeModel, Entity, metaclass=MetaModel):
    """ Main class handling console store's base models (that is, without
         pre-attached fields). """
    pass


class Model(BaseModel):
    """ Main class handling console store's models. """
    source  = CharField()
    created = DateTimeField(default=datetime.datetime.now, null=False)
    updated = DateTimeField(default=datetime.datetime.now, null=False)
    
    @classmethod
    def add_trigger(cls, trig, when, top, op, sql, safe=True):
        """ Add a trigger to model's list of triggers. """
        cls.triggers.append(Trigger(cls, trig, when, top, op, sql, safe))
    
    @classmethod
    def create_table(cls, **options):
        """ Create this table in the bound database."""
        super(Model, cls).create_table(**options)
        for trigger in cls.triggers:
            try:
                cls._meta.database.execute_sql(str(trigger))
            except:
                pass
    
    @classmethod
    def set(cls, **items):
        """ Insert or update a record. """
        items["updated"] = datetime.datetime.now()
        return super(Model, cls).get_or_create(**items)


# ------------------------- ADDITIONAL DATABASE FIELDS -------------------------
class IPAddressField(BigIntegerField):
    """ IPv4/IPv6 address database field. """
    def db_value(self, value):
        if isinstance(value, (str, int)):
            try:
                return int(ip_address(value))
            except Exception:
                pass
        raise ValueError("Invalid IPv4 or IPv6 Address")

    def python_value(self, value):
        return ip_address(value)


class MACAddressField(BigIntegerField):
    """ MAC address database field. """
    def db_value(self, value):
        if isinstance(value, int) and 0 <= value <= 0xffffffffffffffff:
            return value
        elif isinstance(value, str):
            if re.search(r"^([0-9a-f]{2}[:-]){5}[0-9A-F]{2}$", value, re.I):
                return int("".join(re.split(r"[:-]", value)), 16)
        raise ValueError("Invalid MAC Address")

    def python_value(self, value):
        try:
            return ":".join(re.findall("..", "%012x" % value))
        except Exception:
            raise ValueError("Invalid MAC Address")
