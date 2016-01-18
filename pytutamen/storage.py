# -*- coding: utf-8 -*-


# Andy Sayler
# 2016
# pytutamen Package
# Storage Client


### Imports ###

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *

import uuid

from . import config
from . import base


### Constants ###

TYPE_SRV_COL = "server-collection"
TYPE_COL = "collection"

PERM_SRV_COL_CREATE = "srv-col-create"
PERM_COL_CREATE = "col-create"
PERM_COL_READ = "col-read"

_KEY_COL = "collections"
_KEY_COL_SEC = "secrets"


### Exceptions ###

class StorageServerConnectionException(base.ServerConnectionException):
    pass


### Connection Objects ###

class StorageServerConnection(base.ServerConnection):

    def __init__(self, storage_server_name=None, conf=None, conf_path=None, **kwargs):

        # Setup Conf
        if not conf:
            conf = config.ClientConfig(conf_path=conf_path)

        # Get Storage Server Name
        if not storage_server_name:
            storage_server_name = conf.defaults_get_storage_server()
            if not storage_server_name:
                raise(StorageServerConnectionException("Missing Storage Server Name"))

        # Get Storage Server URL
        storage_server_url = conf.storage_server_get_url(storage_server_name)
        if not storage_server_url:
            raise(StorageServerConnectionException("Missing Storage Server URL"))

        # Call Parent
        super().__init__(server_url=storage_server_url, server_name=storage_server_name,
                         conf=conf, conf_path=conf_path, no_client_crt=True, **kwargs)


### Client Objects ###

class StorageClient(object):

    def __init__(self, storage_connection):

        # Check Args
        if not isinstance(storage_connection, StorageServerConnection):
            msg = "'storage_connection' must of an instance of '{}'".format(StorageServerConnection)
            raise(TypeError(msg))

        # Call Parent
        super().__init__()

        # Setup Properties
        self._storage_connection = storage_connection

class CollectionsClient(StorageClient):

    @property
    def objtype(self):
        return TYPE_SRV_COL

    @property
    def objperm_create(self):
        return PERM_SRV_COL_CREATE

    def create(self, tokens, ac_servers, userdata=None, uid=None):

        if not isinstance(tokens, list):
            raise TypeError("tokens must be list")
        if not isinstance(ac_servers, list):
            raise TypeError("ac_servers must be list")

        ep = "{}".format(_KEY_COL)

        json_out = {'ac_servers': ac_servers}
        if userdata:
            json_out['userdata'] = userdata
        if uid:
            json_out['uid'] = str(uid)

        res = self._storage_connection.http_post(ep, json=json_out, tokens=tokens)
        res_uid = uuid.UUID(res[_KEY_COL][0])
        if uid:
            assert uid == res_uid

        return res_uid

class SecretsClient(StorageClient):

    @property
    def objtype(self):
        return TYPE_COL

    @property
    def objperm_create(self):
        return PERM_COL_CREATE

    def create(self, tokens, col_uid, data, userdata=None, uid=None):

        if not isinstance(tokens, list):
            raise TypeError("tokens must be list")
        if not isinstance(col_uid, uuid.UUID):
            raise TypeError("col_uid must be uuid")
        if not isinstance(data, str):
            raise TypeError("data must be string")

        ep = "{}/{}/{}".format(_KEY_COL, str(col_uid), _KEY_COL_SEC)

        json_out = {'data': data}
        if userdata:
            json_out['userdata'] = userdata
        if uid:
            json_out['uid'] = str(uid)

        res = self._storage_connection.http_post(ep, json=json_out, tokens=tokens)
        res_uid = uuid.UUID(res[_KEY_COL_SEC][0])
        if uid:
            assert uid == res_uid

        return res_uid

    @property
    def objperm_fetch(self):
        return PERM_COL_READ

    def fetch(self, tokens, col_uid, key_uid):

        if not isinstance(tokens, list):
            raise TypeError("tokens must be list")
        if not isinstance(col_uid, uuid.UUID):
            raise TypeError("col_uid must be uuid")
        if not isinstance(key_uid, uuid.UUID):
            raise TypeError("key_uid must be uuid")

        ep = "{}/{}/{}/{}/versions/latest".format(_KEY_COL, col_uid, _KEY_COL_SEC, key_uid)
        sec = self._storage_connection.http_get(ep, tokens=tokens)
        return sec
