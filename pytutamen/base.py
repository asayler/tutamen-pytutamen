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

import os
import os.path

import requests


### Constants ###

_API_BASE = 'api'
_API_VERSION = 'v1'
_TOKENS_DELIMINATOR = ':'
_TOKENS_HEADER = 'tutamen-tokens'


### Exceptions ###

class ServerConnectionException(Exception):
    pass

class ClientException(Exception):
    pass


### Objects ###

class ServerConnection(object):

    def __init__(self, server_url=None, server_name=None, server_ca_crt_path=None,
                 account_uid=None, client_uid=None, no_client_crt=False,
                 conf=None, conf_path=None):

        # Check Args
        if not server_url:
            raise(ServerConnectionException("server_url required"))
        if not server_name:
            raise(ServerConnectionException("server_name required"))

        # Call Parent
        super().__init__()

        # Setup Properties
        self._url_server = server_url
        self._path_ca = server_ca_crt_path
        self._session = None

        # Setup Conf
        if not conf:
            conf = config.ClientConfig(conf_path=conf_path)
        self._conf = conf

        # Get UIDs
        if not account_uid:
            account_uid = conf.defaults_get_account_uid()
            if not account_uid:
                raise(ACServerConnectionException("Missing Default Account UID"))
        self._account_uid = account_uid
        if not client_uid:
            client_uid = conf.defaults_get_client_uid()
            if not client_uid:
                raise(ACServerConnectionException("Missing Default Client UID"))
        self._client_uid = client_uid

        # Get Certs
        if not no_client_crt:

            client_key_path = conf.path_client_key(account_uid, client_uid)
            if not os.path.isfile(client_key_path):
                raise(ServerConnectionException("Missing Client Key"))
            self._client_key_path = client_key_path

            client_crt_path = conf.path_client_crt(account_uid, client_uid, server_name)
            if not os.path.isfile(client_crt_path):
                raise(ServerConnectionException("Missing Client Cert"))
            self._client_crt_path = client_crt_path

        else:
            self._client_key_path = None
            self._client_crt_path = None

    def open(self):
        if not self._session:
            ses = requests.Session()
            if self._path_ca:
                ses.verify = self._path_ca
            else:
                ses.verify = True
            if self._client_crt_path and self._client_key_path:
                ses.cert = (self._client_crt_path, self._client_key_path)
            self._session = ses

    def close(self):
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    @property
    def is_open(self):
        return bool(self._session)

    @property
    def url_srv(self):
        return self._url_server

    @property
    def url_api(self):
        return "{}/{}/{}".format(self.url_srv, _API_BASE, _API_VERSION)

    def _tokens_to_header(self, tokens=None):

        if tokens is None:
            tokens = []

        tokens_str = ""
        for token in tokens:
            tokens_str += token.strip()
            tokens_str += _TOKENS_DELIMINATOR
        tokens_str = tokens_str.strip(_TOKENS_DELIMINATOR)

        header = {_TOKENS_HEADER: tokens_str}
        return header

    def http_post(self, endpoint, json=None, tokens=None, auth=None):
        url = "{:s}/{:s}/".format(self.url_api, endpoint)
        header = self._tokens_to_header(tokens)
        res = self._session.post(url, json=json, headers=header, auth=auth)
        res.raise_for_status()
        return res.json()

    def http_put(self, endpoint, json=None, tokens=None, auth=None):
        url = "{:s}/{:s}/".format(self.url_api, endpoint)
        header = self._tokens_to_header(tokens)
        res = self._session.put(url, json=json, headers=header, auth=auth)
        res.raise_for_status()
        return res.json()

    def http_get(self, endpoint=None, tokens=None, auth=None):
        url = "{:s}/{:s}/".format(self.url_api, endpoint)
        header = self._tokens_to_header(tokens)
        res = self._session.get(url, headers=header, auth=auth)
        res.raise_for_status()
        return res.json()

    def http_delete(self, endpoint=None, tokens=None, auth=None):
        url = "{:s}/{:s}/".format(self.url_api, endpoint)
        header = self._tokens_to_header(tokens)
        res = self._session.delete(url, headers=header, auth=auth)
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

    @property
    def connection(self):
        return self._connection
