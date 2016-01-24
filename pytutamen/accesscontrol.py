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
_DEFAULT_TIMEOUT = 60

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
_VAL_AUTHORIZATIONS_STATUS_DENIED = 'denied'

_EP_VERIFIERS = "verifiers"
_KEY_VERIFIERS = "verifiers"

_EP_PERMISSIONS = "permissions"
_KEY_PERMISSIONS = "permissions"


### Exceptions ###

class ACServerConnectionException(base.ServerConnectionException):
    pass

class AuthorizationException(base.ClientException):
    pass

class AuthorizationDenied(AuthorizationException):

    def __init__(self, uid, status):
        msg = "Authorization '{}' denied: {}".format(uid, status)
        super().__init__(msg)

class AuthorizationFailed(AuthorizationException):

    def __init__(self, uid, status):
        msg = "Authorization '{}' failed: {}".format(uid, status)
        super().__init__(msg)


### Connection Objects ###

class ACServerConnection(base.ServerConnection):

    def __init__(self, server_name=None, conf=None, conf_path=None, **kwargs):

        # Setup Conf
        if not conf:
            conf = config.ClientConfig(conf_path=conf_path)

        # Get Server Name
        if not server_name:
            server_name = conf.defaults_get_ac_server()
            if not server_name:
                raise(ACServerConnectionException("Missing AC Server Name"))

        # Get Server URL
        server_url = conf.ac_server_get_url(server_name)
        if not server_url:
            raise(ACServerConnectionException("Missing AC Server URL"))

        # Call Parent
        super().__init__(server_url=server_url, server_name=server_name,
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

        ep = "{}/{}".format(_EP_BOOTSTRAP, _KEY_ACCOUNTS)

        json_out = {'client_csr': client_csr}
        if account_userdata:
            json_out['account_userdata'] = account_userdata
        if client_userdata:
            json_out['client_userdata'] = client_userdata
        if account_uid:
            json_out['account_uid'] = str(account_uid)
        if client_uid:
            json_out['client_uid'] = str(client_uid)

        res = self._ac_connection.http_post(ep, json=json_out)
        res_account_uid = uuid.UUID(res[_KEY_ACCOUNTS][0])
        if account_uid:
            assert res_account_uid == account_uid

        res_client_uid, res_client_cert = res[_KEY_CLIENTS_CERTS].popitem()
        res_client_uid = uuid.UUID(res_client_uid)
        if client_uid:
            assert res_client_uid == client_uid

        return (res_account_uid, res_client_uid, res_client_cert)

class AuthorizationsClient(AccessControlClient):

    def request(self, obj_type, obj_perm, obj_uid=None, userdata=None):

        if userdata is None:
            userdata = {}

        ep = "{}".format(_EP_AUTHORIZATIONS)

        json_out = {'objperm': obj_perm,
                    'objtype': obj_type,
                    'objuid': str(obj_uid) if obj_uid else "",
                    'userdata': userdata}

        res = self._ac_connection.http_post(ep, json=json_out)
        return uuid.UUID(res[_KEY_AUTHORIZATIONS][0])

    def fetch(self, authz_uid):

        ep = "{}/{}/".format(_KEY_AUTHORIZATIONS, str(authz_uid))

        authz = self._ac_connection.http_get(ep)
        return authz

    def wait_token(self, authz_uid, timeout=_DEFAULT_TIMEOUT):

        authz = self.fetch(authz_uid)
        status = authz[_KEY_AUTHORIZATIONS_STATUS]
        cnt = 0
        while (status == _VAL_AUTHORIZATIONS_STATUS_PENDING):
            if (cnt * _WAIT_SLEEP) > timeout:
                raise Exception("Timed out wating for token")
            time.sleep(_WAIT_SLEEP)
            authz = self.fetch(authz_uid)
            status = authz[_KEY_AUTHORIZATIONS_STATUS]
            cnt += 1
        if (status == _VAL_AUTHORIZATIONS_STATUS_GRANTED):
            return authz[_KEY_AUTHORIZATIONS_TOKEN]
        else:
            return None

class VerifiersClient(AccessControlClient):

    def create(self, uid=None, accounts=None, authenticators=None, userdata=None):

        if uid:
            if not isinstance(uid, uuid.UUID):
                raise TypeError("uid must be uuid.UUID")
        if not accounts:
            accounts = []
        else:
            accounts = [str(a) for a in accounts]
        if not authenticators:
            authenticators = []
        else:
            authenticators = [str(a) for a in authenticators]
        if userdata is None:
            userdata = {}

        ep = "{}".format(_EP_VERIFIERS)

        json_out = {}
        if uid:
            json_out['uid'] = str(uid)
        if accounts:
            json_out['accounts'] = accounts
        if authenticators:
            json_out['authenticators'] = accounts
        if userdata:
            json_out['userdata'] = userdata

        res = self._ac_connection.http_post(ep, json=json_out)
        return uuid.UUID(res[_KEY_VERIFIERS][0])

    def fetch(self, uid):

        if not isinstance(uid, uuid.UUID):
            raise TypeError("uid must be uuid.UUID")

        ep = "{}/{}/".format(_EP_VERIFIERS, str(uid))

        verifier = self._ac_connection.http_get(ep)
        return verifier

class PermissionsClient(AccessControlClient):

    def create(self, objtype, objuid=None,
               v_create=None, v_read=None,
               v_modify=None, v_delete=None,
               v_ac=None, v_default=None):

        if v_create:
            v_create = [str(v) for v in v_create]
        if v_read:
            v_read = [str(v) for v in v_read]
        if v_modify:
            v_modify = [str(v) for v in v_modify]
        if v_delete:
            v_delete = [str(v) for v in v_delete]
        if v_ac:
            v_ac = [str(v) for v in v_ac]
        if v_default:
            v_default = [str(v) for v in v_default]

        ep = "{}".format(_EP_PERMISSIONS)

        json_out = {'objtype': objtype}
        if objuid:
            json_out['objuid'] = str(objuid)
        if v_create:
            json_out['create'] = v_create
        if v_read:
            json_out['read'] = v_read
        if v_modify:
            json_out['modify'] = v_modify
        if v_delete:
            json_out['delete'] = v_delete
        if v_ac:
            json_out['ac'] = v_ac
        if v_default:
            json_out['default'] = v_default

        res = self._ac_connection.http_post(ep, json=json_out)
        res = res[_KEY_PERMISSIONS][0]
        assert(objtype == res['objtype'])
        if objuid:
            assert(objuid == uuid.UUID(res['objuid']))
        return objtype, objuid

    def fetch(self, objtype, objuid):

        ep = "{}/{}/{}/".format(_EP_PERMISSIONS, objtype, str(objuid))

        perms = self._ac_connection.http_get(ep)
        return perms
