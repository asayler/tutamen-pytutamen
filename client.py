### Imports ###

import requests


### Constants ###

_AUTH_WAIT_TIME = 0.1

_KEY_AUTH = "authorizations"
_KEY_AUTH_STATUS = "status"
_KEY_AUTH_TOKEN = "token"
_KEY_COL = "collections"
_KEY_COL_SEC = "secrets"

_VAL_AUTH_STATUS_PENDING = 'pending'
_VAL_AUTH_STATUS_GRANTED = 'granted'

PERM_SRV_COL_CREATE = "srv-col-create"
PERM_COL_CREATE = "col-create"
PERM_COL_READ = "col-read"

### Excpetions ###

class ClientException(Exception):
    pass

### Objects ###

class Client(object):

    def __init__(self, url_server=None, path_cert=None, path_key=None, path_ca=None):

        # Get Args
        if not url_server:
            raise(ClientExcpetion("url_server required"))
        if not path_cert:
            raise(ClientExcpetion("path_cert required"))
        if not path_key:
            raise(ClientExcpetion("path_key required"))
        if not path_ca:
            raise(ClientExcpetion("path_ca required"))

        # Call Parent
        super().__init__()

        # Setup Properties
        self._url_server = url_server
        self._path_cert = path_cert
        self._path_key = path_key
        self._path_ca = path_ca

    def open(self):
        ses = requests.Session()
        ses.verify = self._path_ca
        ses.cert = (self._path_cert, self._path_key)
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

    def http_post(self, endpoint, json=None, token=None):
        auth = self._token_to_auth(token)
        url = "{:s}/{:s}/".format(self._url_server, endpoint)
        res = self._session.post(url, json=json, auth=auth)
        res.raise_for_status()
        return res.json()

    def http_put(self, endpoint, json=None, token=None):
        auth = self._token_to_auth(token)
        url = "{:s}/{:s}/".format(self._url_server, endpoint)
        res = self._session.put(url, json=json, auth=auth)
        res.raise_for_status()
        return res.json()

    def http_get(self, endpoint=None, token=None):
        auth = self._token_to_auth(token)
        url = "{:s}/{:s}/".format(self._url_server, endpoint)
        res = self._session.get(url, auth=auth)
        res.raise_for_status()
        return res.json()

    def http_delete(self, endpoint=None, token=None):
        auth = self._token_to_auth(token)
        url = "{:s}/{:s}/".format(self._url_server, endpoint)
        res = self._session.delete(url, auth=auth)
        res.raise_for_status()
        return res.json()

class ObjectClient(object):

    def __init__(self, client):

        # Check Args
        if not isinstance(client, Client):
            raise(TypeError("'client' must of an instance of {}".format(Client)))

        # Call Parent
        super().__init__()

        # Setup Properties
        self._client = client

class AuthorizationsClient(ObjectClient):

    def request(self, permission, metadata={}):

        ep = "{}".format(_KEY_AUTH)
        json_out = {'permission': permission, 'metadata': metadata}
        res = self._client.http_post(ep, json=json_out)
        return res[_KEY_AUTH][0]

    def status(self, ath_uid):

        ep = "{}/{}/{}".format(_KEY_AUTH, ath_uid, _KEY_AUTH_STATUS)
        res = self._client.http_get(ep)
        return res[_KEY_AUTH_STATUS]

    def token(self, ath_uid):

        ep = "{}/{}/{}".format(_KEY_AUTH, ath_uid, _KEY_AUTH_TOKEN)
        res = self._client.http_get(ep)
        return res[_KEY_AUTH_TOKEN]

    def request_wait(self, permission, metadata={}):

        ath_uid = self.request(permission, metadata=metadata)
        status = self.status(ath_uid)
        while (status == _VAL_AUTH_STATUS_PENDING):
            time.sleep(_AUTH_WAIT_SLEEP)
            status = self.status(ath_uid)
        if (status == _VAL_AUTH_STATUS_GRANTED):
            return self.token(ath_uid)
        else:
            return None

class CollectionsClient(ObjectClient):

    def create(self, metadata={}, token=None):

        if not token:
            a = AuthorizationsClient(self._client)
            token = a.request_wait(PERM_SRV_COL_CREATE)
            if not token:
                raise ClientException("Authorization Denied")

        ep = "{}".format(_KEY_COL)
        json_out = {'metadata': metadata}
        res = self._client.http_post(ep, json=json_out, token=token)
        return res[_KEY_COL][0]

class SecretsClient(ObjectClient):

    def create(self, col_uid, data, metadata={}, token=None):

        if not token:
            a = AuthorizationsClient(self._client)
            token = a.request_wait(PERM_COL_CREATE)
            if not token:
                raise ClientException("Authorization Denied")

        ep = "{}/{}/{}".format(_KEY_COL, col_uid, _KEY_COL_SEC)
        json_out = {'data': data, 'metadata': metadata}
        res = self._client.http_post(ep, json=json_out, token=token)
        return res[_KEY_COL_SEC][0]

    def data(self, col_uid, key_uid, version=None, token=None):

        if not token:
            a = AuthorizationsClient(self._client)
            token = a.request_wait(PERM_COL_READ)
            if not token:
                raise ClientException("Authorization Denied")

        ep = "{}/{}/{}/{}/versions/latest".format(_KEY_COL, col_uid, _KEY_COL_SEC, key_uid)
        res = self._client.http_get(ep, token=token)
        return res['data']
