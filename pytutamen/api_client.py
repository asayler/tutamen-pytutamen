# -*- coding: utf-8 -*-


# Andy Sayler
# 2015
# pytutamen Package
# Tutamen Client Library


### Imports ###

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *

import requests


### Constants ###

_AUTH_WAIT_SLEEP = 0.1

_KEY_AUTH = "authorizations"
_KEY_AUTH_STATUS = "status"
_KEY_AUTH_TOKEN = "token"
_KEY_COL = "collections"
_KEY_COL_SEC = "secrets"

_VAL_AUTH_STATUS_PENDING = 'pending'
_VAL_AUTH_STATUS_GRANTED = 'granted'

_API_BASE = 'api'
_API_VERSION = 'v1'

PERM_SRV_COL_CREATE = "srv-col-create"
PERM_COL_CREATE = "col-create"
PERM_COL_READ = "col-read"


### Exceptions ###

class ServerConnectionException(Exception):
    pass


### Objects ###

class ServerConnection(object):

    def __init__(self, server_url=None, server_ca_crt_path=None,
                 client_crt_path=None, client_key_path=None):

        # Get Args
        if not server_url:
            raise(ServerConnectionException("server_rul required"))

        # Call Parent
        super().__init__()

        # Setup Properties
        self._url_server = server_url
        self._path_ca = server_ca_crt_path
        self._path_key = client_key_path
        self._path_crt = client_crt_path

    def open(self):
        ses = requests.Session()
        if self._path_ca:
            ses.verify = self._path_ca
        else:
            ses.verify = True
        if self._path_crt and self._path_key:
            ses.cert = (self._path_crt, self._path_key)
        self._session = ses

    def close(self):
        self._session.close()
        del(self._session)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def _token_to_auth(self, token):
        if token:
            auth = requests.auth.HTTPBasicAuth(token, '')
        else:
            auth = None
        return auth

    @property
    def url_srv(self):
        return self._url_server

    @property
    def url_api(self):
        return "{}/{}/{}".format(self.url_srv, _API_BASE, _API_VERSION)

    def http_post(self, endpoint, json=None, token=None):
        auth = self._token_to_auth(token)
        url = "{:s}/{:s}/".format(self.url_api, endpoint)
        res = self._session.post(url, json=json, auth=auth)
        res.raise_for_status()
        return res.json()

    def http_put(self, endpoint, json=None, token=None):
        auth = self._token_to_auth(token)
        url = "{:s}/{:s}/".format(self.url_api, endpoint)
        res = self._session.put(url, json=json, auth=auth)
        res.raise_for_status()
        return res.json()

    def http_get(self, endpoint=None, token=None):
        auth = self._token_to_auth(token)
        url = "{:s}/{:s}/".format(self.url_api, endpoint)
        res = self._session.get(url, auth=auth)
        res.raise_for_status()
        return res.json()

    def http_delete(self, endpoint=None, token=None):
        auth = self._token_to_auth(token)
        url = "{:s}/{:s}/".format(self.url_api, endpoint)
        res = self._session.delete(url, auth=auth)
        res.raise_for_status()
        return res.json()

class ObjectClient(object):

    def __init__(self, connection):

        # Check Args
        if not isinstance(connection, ServerConnection):
            raise(TypeError("'connection' must of an instance of {}".format(ServerConnection)))

        # Call Parent
        super().__init__()

        # Setup Properties
        self._connection = connection

class AuthorizationsClient(ObjectClient):

    def request(self, permission, userdata={}):

        ep = "{}".format(_KEY_AUTH)
        json_out = {'permission': permission, 'userdata': userdata}
        res = self._connection.http_post(ep, json=json_out)
        return res[_KEY_AUTH][0]

    def status(self, ath_uid):

        ep = "{}/{}/{}".format(_KEY_AUTH, ath_uid, _KEY_AUTH_STATUS)
        res = self._connection.http_get(ep)
        return res[_KEY_AUTH_STATUS]

    def token(self, ath_uid):

        ep = "{}/{}/{}".format(_KEY_AUTH, ath_uid, _KEY_AUTH_TOKEN)
        res = self._connection.http_get(ep)
        return res[_KEY_AUTH_TOKEN]

    def request_wait(self, permission, userdata={}):

        ath_uid = self.request(permission, userdata=userdata)
        status = self.status(ath_uid)
        while (status == _VAL_AUTH_STATUS_PENDING):
            time.sleep(_AUTH_WAIT_SLEEP)
            status = self.status(ath_uid)
        if (status == _VAL_AUTH_STATUS_GRANTED):
            return self.token(ath_uid)
        else:
            return None

class CollectionsClient(ObjectClient):

    def create(self, userdata={}, token=None):

        if not token:
            a = AuthorizationsClient(self._connection)
            token = a.request_wait(PERM_SRV_COL_CREATE)
            if not token:
                raise ClientException("Authorization Denied")

        ep = "{}".format(_KEY_COL)
        json_out = {'userdata': userdata}
        res = self._connection.http_post(ep, json=json_out, token=token)
        return res[_KEY_COL][0]

class SecretsClient(ObjectClient):

    def create(self, col_uid, data, userdata={}, token=None):

        if not token:
            a = AuthorizationsClient(self._connection)
            token = a.request_wait(PERM_COL_CREATE)
            if not token:
                raise ClientException("Authorization Denied")

        ep = "{}/{}/{}".format(_KEY_COL, col_uid, _KEY_COL_SEC)
        json_out = {'data': data, 'userdata': userdata}
        res = self._connection.http_post(ep, json=json_out, token=token)
        return res[_KEY_COL_SEC][0]

    def data(self, col_uid, key_uid, version=None, token=None):

        if not token:
            a = AuthorizationsClient(self._connection)
            token = a.request_wait(PERM_COL_READ)
            if not token:
                raise ClientException("Authorization Denied")

        ep = "{}/{}/{}/{}/versions/latest".format(_KEY_COL, col_uid, _KEY_COL_SEC, key_uid)
        res = self._connection.http_get(ep, token=token)
        return res['data']
