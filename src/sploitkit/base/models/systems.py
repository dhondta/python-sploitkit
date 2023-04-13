# -*- coding: UTF-8 -*-
from sploitkit import *


class Host(Model):
    hostname = CharField(max_length=256)
    ip       = IPAddressField()
    mac      = MACAddressField()
    os       = CharField()
    location = CharField()
    
    class Meta:
        indexes = ((("hostname", "ip", "mac"), True),)


class Port(Model):
    number = IntegerField(primary_key=True)
    status = BooleanField()


class Service(Model):
    name = CharField(primary_key=True)


class HostPort(BaseModel):
    host = ForeignKeyField(Host, backref="ports")
    port = ForeignKeyField(Port, backref="hosts")
    
    class Meta:
        primary_key = CompositeKey("host", "port")


class ServicePort(BaseModel):
    service = ForeignKeyField(Service, backref="ports")
    port    = ForeignKeyField(Port, backref="services")
    
    class Meta:
        primary_key = CompositeKey("service", "port")

