from __future__ import unicode_literals

import re
import types
from collections import OrderedDict

try:
    from playhouse.sqlcipher_ext import Model, ModelBase, SqlCipherDatabase as SqliteDB
    enc_enabled = (True, "")
except ImportError as e:
    from peewee import Model, ModelBase, SqliteDatabase as SqliteDB
    enc_enabled = (False, str(e))

from ..entity import Entity, MetaEntityBase
from ...utils.password import input_password


__all__ = ["StoreExtension", "StoragePool"]


class Store(SqliteDB):
    """ Storage database class. """
    def __init__(self, path, *args, **kwargs):
        self.path = str(path)  # ensure the input is str, e.g. not Path
        kwargs.setdefault('pragmas', {})
        # enable automatic VACUUM (to regularly defragment the DB)
        kwargs['pragmas'].setdefault('auto_vacuum', 1)
        # set page cache size (in KiB)
        kwargs['pragmas'].setdefault('cache_size', -64000)
        # allow readers and writers to co-exist
        kwargs['pragmas'].setdefault('journal_mode', "wal")
        # enforce foreign-key constraints
        kwargs['pragmas'].setdefault('foreign_keys', 1)
        # enforce CHECK constraints
        kwargs['pragmas'].setdefault('ignore_check_constraints', 0)
        # let OS handle fsync
        kwargs['pragmas'].setdefault('synchronous', 0)
        # force every transaction in exclusive mode
        kwargs['pragmas'].setdefault('locking_mode', 1)
        super(Store, self).__init__(path, *args, **kwargs)
    
    def __getattr__(self, name):
        """ Override getattr to handle add_* store methods. """
        if re.match(r"^[gs]et_", name):
            model = "".join(w.capitalize() for w in name.split("_")[1:])
            cls = self.get_model(model)
            if cls is not None:
                if name.startswith("get"):
                    return cls.get
                elif hasattr(cls, "set"):
                    return cls.set
        raise AttributeError
    
    def get_model(self, name, base=False):
        """ Get a model class from its name. """
        return Entity.get_subclass("model", name) or \
               Entity.get_subclass("basemodel", name)
        
    @property
    def basemodels(self):
        """ Shortcut for the list of BaseModel subclasses. """
        return Entity._subclasses.key("basemodel")
        
    @property
    def models(self):
        """ Shortcut for the list of Model subclasses. """
        return Entity._subclasses.key("model")
    
    @property
    def volatile(self):
        """ Simple attribute for telling if the DB is in memory. """
        return self.path == ":memory:"


class StoreExtension(Entity, metaclass=MetaEntityBase):
    """ Dummy class handling store extensions for the Store class. """
    pass


class StoragePool(object):
    """ Storage pool class. """
    __pool    = []
    encrypted = enc_enabled
    models    = []
    
    def close(self, remove=False):
        """ Close every database in the pool. """
        for db in self.__pool[::-1]:
            self.remove(db) if remove else db.close()
    
    def free(self):
        """ Close and remove every database in the pool. """
        self.close(True)
    
    def get(self, path, *args, **kwargs):
        """ Get a database from the pool ; if the DB does not exist yet, create
             and register it. """
        path = str(path)  # ensure the input is str, e.g. not a Path instance
        try:
            db = [_ for _ in self.__pool if _.path == path][0]
        except IndexError:
            if enc_enabled[0]:
                kwargs['passphrase'] = input_password()
            classes = tuple([Store] + StoreExtension.subclasses)
            db = Store(path, *args, **kwargs)
            db.__class__ = type("ExtendedStore", classes, {})
            # in 'classes', StoreExtension subclasses will be present, therefore
            #  making ExtendedStore registered in its list of subclasses ; this
            #  line prevents from having multiple combined classes having the
            #  same Store base class
            StoreExtension.unregister_subclass(db.__class__)
            self.__pool.append(db)
            for m in self.models:
                m.bind(db)
            db.create_tables(self.models, safe=True)
            db.close()  # commit and save the created tables
            db.connect()
        return db
    
    def remove(self, db):
        """ Remove a database from the pool. """
        db.close()
        self.__pool.remove(db)
        del db


# source: https://stackoverflow.com/questions/34142550/sqlite-triggers-datetime-defaults-in-sql-ddl-using-peewee-in-python
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
