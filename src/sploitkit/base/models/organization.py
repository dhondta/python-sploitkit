# -*- coding: UTF-8 -*-
from sploitkit import *
from sploitkit.base.models.users import Email, User


class Organization(Model):
    name = CharField(primary_key=True)


class Unit(Model):
    name         = CharField(primary_key=True)
    organization = ForeignKeyField(Organization, backref="units")


class Employee(Model):
    firstname = CharField()
    lastname  = CharField()
    role      = CharField()
    title     = CharField()
    
    class Meta:
        indexes = ((("firstname", "lastname", "role"), True),)
    
    @property
    def fullname(self):
        return f"{self.firstname} {self.lastname} ({self.role})"


class EmployeeUnit(BaseModel):
    employee = ForeignKeyField(Employee, backref="units")
    unit     = ForeignKeyField(Unit, backref="employees")
    
    class Meta:
        primary_key = CompositeKey("employee", "unit")


class EmployeeEmail(BaseModel):
    employee = ForeignKeyField(Employee, backref="emails")
    email    = ForeignKeyField(Email, backref="employees")
    
    class Meta:
        primary_key = CompositeKey("employee", "email")


class EmployeeUser(BaseModel):
    employee = ForeignKeyField(Employee, backref="users")
    user     = ForeignKeyField(User, backref="employees")
    
    class Meta:
        primary_key = CompositeKey("employee", "user")

