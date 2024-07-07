# -*- coding: UTF-8 -*-
from peewee import SqliteDatabase


__all__ = ["StoragePool"]


class StoragePool(object):
    """ Storage pool class. """
    __pool = []
    
    def __init__(self, ext_class=None):
        self._entity_class = getattr(ext_class(), "base_class", None)
        self._ext_class = ext_class
    
    def close(self, remove=False):
        """ Close every database in the pool. """
        for db in self.__pool[::-1]:
            self.remove(db) if remove else db.close()
    
    def free(self):
        """ Close and remove every database in the pool. """
        self.close(True)
    
    def get(self, path, *args, **kwargs):
        """ Get a database from the pool ; if the DB does not exist yet, create and register it. """
        path = str(path)  # ensure the input is str, e.g. not a Path instance
        try:
            db = [_ for _ in self.__pool if _.path == path][0]
        except IndexError:
            classes = tuple([Store] + self.extensions)
            cls = type("ExtendedStore", classes, {})
            db = cls(path, *args, **kwargs)
            db._pool = self
            # as the store extension class should subclass Entity, in 'classes', store extension subclasses will be
            #  present, therefore making ExtendedStore registered in its list of subclasses ; this line prevents from
            #  having multiple combined classes having the same Store base class
            if self._ext_class is not None and hasattr(self._ext_class, "unregister_subclass"):
                self._ext_class.unregister_subclass(cls)
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
        delattr(db, "_pool")
        self.__pool.remove(db)
        del db
    
    @property
    def extensions(self):
        """ Get the list of store extension subclasses. """
        try:
            return self._ext_class.subclasses
        except AttributeError:
            return []


class Store(SqliteDatabase):
    """ Storage database class. """
    def __init__(self, path, *args, **kwargs):
        self.path = str(path)  # ensure the input is str, e.g. not Path
        self._last_snapshot = 0
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
        from re import match
        if name == "basemodels":
            BaseModel = self._pool._entity_class._subclasses["basemodel"]
            return self._pool._entity_class._subclasses[BaseModel]
        elif name == "models":
            Model = self._pool._entity_class._subclasses["model"]
            return self._pool._entity_class._subclasses[Model]
        elif name == "volatile":
            return self.path == ":memory:"
        elif match(r"^[gs]et_[a-z]+", name) and name != "model":
            model = "".join(w.capitalize() for w in name.split("_")[1:])
            cls = self.get_model(model)
            if cls is not None:
                if name.startswith("get"):
                    return cls.get
                elif hasattr(cls, "set"):
                    return cls.set
        raise AttributeError("Store object has no attribute %r" % name)
    
    def get_model(self, name, base=False):
        """ Get a model class from its name. """
        return self._pool._entity_class.get_subclass("model", name) or \
               self._pool._entity_class.get_subclass("basemodel", name)
    
    def snapshot(self, save=True):
        """ Snapshot the store in order to be able to get back to this state afterwards if the results are corrupted by
             a module OR provide the reference number of the snapshot to get back to, and remove every other snapshot
             after this number. """
        if not save and self._last_snapshot == 0:
            return
        self.close()
        if save:
            self._last_snapshot += 1
        s = f"{self.path}.snapshot{self._last_snapshot}"
        from shutil import copy
        copy(self.path, s) if save else copy(s, self.path)
        if not save:
            from os import remove
            remove("{}.snapshot{}".format(self.path, self._last_snapshot))
            self._last_snapshot -= 1
        self.connect()

