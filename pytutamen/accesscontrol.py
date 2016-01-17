# -*- coding: utf-8 -*-


# Andy Sayler
# 2016
# pytutamen Package
# Access Control Client


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

_WAIT_SLEEP = 0.1

_EP_BOOTSTRAP = "bootstrap"

_KEY_ACCOUNTS = "accounts"

_KEY_CLIENTS = "clients"
_KEY_CLIENTS_CERTS = "{}_certs".format(_KEY_CLIENTS)

_EP_AUTHORIZATIONS = "authorizations"
_KEY_AUTHORIZATIONS = "authorizations"
_KEY_AUTHORIZATIONS_STATUS = "status"
_KEY_AUTHORIZATIONS_TOKEN = "token"
_VAL_AUTHORIZATIONS_STATUS_PENDING = 'pending'
_VAL_AUTHORIZATIONS_STATUS_GRANTED = 'approved'


### Exceptions ###

class ACServerConnectionException(base.ServerConnectionException):
    pass


### Connection Objects ###

class ACServerConnection(base.ServerConnection):

    def __init__(self, ac_server_name=None, conf=None, conf_path=None, **kwargs):

        # Setup Conf
        if not conf:
            conf = config.ClientConfig(conf_path=conf_path)

        # Get Server Name
        if not ac_server_name:
            ac_server_name = conf.defaults_get_ac_server()
            if not ac_server_name:
                raise(ACServerConnectionException("Missing AC Server Name"))

        # Get Server URL
        ac_server_url = conf.ac_server_get_url(ac_server_name)
        if not ac_server_url:
            raise(ACServerConnectionException("Missing AC Server URL"))

        # Call Parent
        super().__init__(server_url=ac_server_url, server_name=ac_server_name,
                         conf=conf, conf_path=conf_path, **kwargs)

### Client Objects ###

class AccessControlClient(object):

    def __init__(self, ac_connection):

        # Check Args
        if not isinstance(ac_connection, ACServerConnection):
            raise(TypeError("'ac_connection' must of an instance of {}".format(ACServerConnection)))

        # Call Parent
        super().__init__()

        # Setup Properties
        self._ac_connection = ac_connection

class BootstrapClient(AccessControlClient):

    def account(self, account_userdata=None, account_uid=None,
                client_userdata=None, client_uid=None, client_csr=None):

        if not client_csr:
            raise ValueError("client_csr required")
        if account_userdata is None:
            account_userdata = {}
        if client_userdata is None:
            client_userdata = {}

        ep = "{}/{}".format(_EP_BOOTSTRAP, _KEY_ACCOUNTS)

        json_out = {'account_userdata': account_userdata,
                    'client_userdata': client_userdata}
        if account_uid:
            json_out['account_uid'] = str(account_uid)
        if client_uid:
            json_out['client_uid'] = str(client_uid)
        json_out['client_csr'] = client_csr

        res = self._ac_connection.http_post(ep, json=json_out)
        account_uid = uuid.UUID(res[_KEY_ACCOUNTS][0])
        client_uid, client_cert = res[_KEY_CLIENTS_CERTS].popitem()
        client_uid = uuid.UUID(client_uid)
        return (account_uid, client_uid, client_cert)

class AuthorizationsClient(AccessControlClient):

    def request(self, obj_type, obj_uid, obj_perm, userdata=None):

        if userdata is None:
            userdata = {}

        ep = "{}".format(_EP_AUTHORIZATIONS)

        json_out = {'objperm': obj_perm,
                    'objtype': obj_type,
                    'objuid': str(obj_uid),
                    'userdata': userdata}

        res = self._ac_connection.http_post(ep, json=json_out)
        return uuid.UUID(res[_KEY_AUTHORIZATIONS][0])

    def fetch(self, auth_uid):

        ep = "{}/{}/".format(_KEY_AUTHORIZATIONS, str(auth_uid))

        auth = self._ac_connection.http_get(ep)
        return auth

    def wait_token(self, auth_uid):

        auth = self.fetch(auth_uid)
        status = auth[_KEY_AUTHORIZATIONS_STATUS]
        while (status == _VAL_AUTHORIZATIONS_STATUS_PENDING):
            time.sleep(_WAIT_SLEEP)
            auth = self.fetch(auth_uid)
            status = auth[_KEY_AUTHORIZATIONS_STATUS]
        if (status == _VAL_AUTHORIZATIONS_STATUS_GRANTED):
            return auth[_KEY_AUTHORIZATIONS_TOKEN]
        else:
            return None
