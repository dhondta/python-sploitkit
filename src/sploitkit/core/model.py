# -*- coding: UTF-8 -*-
import datetime
from peewee import *
from peewee import Model as PeeweeModel, ModelBase

from .components.logger import get_logger
from .entity import Entity, MetaEntityBase


__all__ = ["BaseModel", "Model", "StoreExtension"]


logger = get_logger("core.model")


class MetaModel(ModelBase, MetaEntityBase):
    """ Metaclass of a Model. """
    triggers = []
    
    def __new__(meta, name, bases, clsdict):
        subcls = ModelBase.__new__(meta, name, bases, clsdict)
        if subcls.__name__ != "Model":
            pass
            # add triggers here
            #try:
            #    trigger = f"{subcls._meta.table_name}_updated"
            #    subcls.add_trigger(trigger, "AFTER", "UPDATE", "UPDATE", "SET updated=CURRENT_TIMESTAMP")
            #except AttributeError:
            #    pass
        return subcls
    
    def __repr__(self):
        return "<%s: %s>" % (self.entity.capitalize(), self.__name__)


class BaseModel(PeeweeModel, Entity, metaclass=MetaModel):
    """ Main class handling console store's base models (that is, without pre-attached fields). """
    pass


class Model(BaseModel):
    """ Main class handling console store's models. """
    source  = CharField(null=True)
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


class StoreExtension(Entity, metaclass=MetaEntityBase):
    """ Dummy class handling store extensions for the Store class. """
    pass


# source:
#  https://stackoverflow.com/questions/34142550/sqlite-triggers-datetime-defaults-in-sql-ddl-using-peewee-in-python
class Trigger(object):
    """Trigger template wrapper for use with peewee ORM."""
    _template = """
    {create} {name} {when} {trigger_op}
    ON {tablename}
    BEGIN
        {op} {tablename} {sql} WHERE {pk}={old_new}.{pk};
    END;
    """

    def __init__(self, table, name, when, trigger_op, op, sql, safe=True):
        self.create = "CREATE TRIGGER" + (" IF NOT EXISTS" if safe else "")
        self.tablename = table._meta.name
        self.pk = table._meta.primary_key.name
        self.name = name
        self.when = when
        self.trigger_op = trigger_op
        self.op = op
        self.sql = sql
        self.old_new = "new" if trigger_op.lower() == "insert" else "old"

    def __str__(self):
        return self._template.format(**self.__dict__)

