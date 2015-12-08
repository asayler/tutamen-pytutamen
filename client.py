### Imports ###

import sys
import json
import os
import uuid

import requests


### Constants ###

_AUTHORIZATIONS_KEY = "authorizations"
_COLLECTIONS_KEY = "collections"
_SECRETS_KEY = "secrets"


### Excpetions ###

class ClientException(Exception):
    pass

### Objects ###

class Client(object):

    def __init__(self, url_server=None, path_cert=None, path_key=None, path_ca=None):

        # Call Parent
        super().__init__()

        # Get Args
        if not url_server:
            raise(ClientExcpetion("url_server required"))
        if not path_cert:
            raise(ClientExcpetion("path_cert required"))
        if not path_key:
            raise(ClientExcpetion("path_key required"))
        if not path_ca:
            raise(ClientExcpetion("path_ca required"))

        # Setup Properties
        self._url_server = url_server
        self._path_cert = path_cert
        self._path_key = path_key
        self._path_ca = path_ca

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def http_post(self, endpoint, json=None, auth=None):
        url = "{:s}/{:s}/".format(self._url_server, endpoint)
        res = requests.post(url, json=json,
                            verify=self._path_ca, auth=auth,
                            cert=(self._path_cert, self._path_key))
        res.raise_for_status()
        return res.json()

    def http_put(self, endpoint, json=None, auth=None):
        url = "{:s}/{:s}/".format(self._url_server, endpoint)
        res = requests.put(url, json=json,
                           verify=self._path_ca, auth=auth,
                           cert=(self._path_cert, self._path_key))
        res.raise_for_status()
        return res.json()

    def http_get(self, endpoint=None, auth=None):
        url = "{:s}/{:s}/".format(self._url_server, endpoint)
        res = requests.get(url,
                           verify=self._path_ca, auth=auth,
                           cert=(self._path_cert, self._path_key))
        res.raise_for_status()
        return res.json()

    def http_delete(self, endpoint=None, auth=None):
        url = "{:s}/{:s}/".format(self._url_server, endpoint)
        res = requests.delete(url,
                              verify=self._path_ca, auth=auth,
                              cert=(self._path_cert, self._path_key))
        res.raise_for_status()
        return res.json()
