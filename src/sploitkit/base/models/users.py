# -*- coding: UTF-8 -*-
from sploitkit import *


class User(Model):
    username = CharField(primary_key=True)


class Email(Model):
    address = CharField(primary_key=True, max_length=320)


class Password(Model):
    hash  = CharField(primary_key=True)
    plain = CharField()


class UserEmail(BaseModel):
    user  = ForeignKeyField(User, backref="emails")
    email = ForeignKeyField(Email, backref="users")
    
    class Meta:
        primary_key = CompositeKey("user", "email")


class UserPassword(BaseModel):
    user     = ForeignKeyField(User, backref="passwords")
    password = ForeignKeyField(Password, backref="users")
    
    class Meta:
        primary_key = CompositeKey("user", "password")


#TODO: to be tested
#class UsersStorage(StoreExtension):
#    def set_user(self, username):
#        User.get_or_create(username=username).execute()


#TODO: to be tested
#class PasswordsStorage(StoreExtension):
#    def set_password(self, password):
#        Password.insert(password=password).execute()

