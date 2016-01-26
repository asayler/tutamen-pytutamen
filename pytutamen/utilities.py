# -*- coding: utf-8 -*-


# Andy Sayler
# 2016
# pytutamen Package
# Utility Functions


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
from . import crypto
from . import constants
from . import accesscontrol
from . import storage


### Constants ###

_DEFAULT_COUNTRY = 'US'
_DEFAULT_STATE = 'Colorado'
_DEFAULT_LOCALITY = 'Boulder'


### Config Functions ###

def config_new_ac_server(name, url, conf=None, conf_path=None):

    # Setup Conf
    if not conf:
        conf = config.ClientConfig(conf_path=conf_path)

    # Save Server Config
    if conf.ac_server_configured(name):
        old_url = conf.ac_server_get_url(name)
        if url != old_url:
            msg = "AC Server '{}' already configured with different URL".format(name)
            raise Exception(msg)
    else:
        conf.ac_server_set_url(name, url)

    # Update Defaults
    if not conf.defaults_get_ac_server():
        conf.defaults_set_ac_server(name)

def config_new_storage_server(name, url, conf=None, conf_path=None):

    # Setup Conf
    if not conf:
        conf = config.ClientConfig(conf_path=conf_path)

    # Save Server Config
    if conf.storage_server_configured(name):
        old_url = conf.storage_server_get_url(name)
        if url != old_url:
            msg = "Storage Server '{}' already configured with different URL".format(name)
            raise Exception(msg)
    else:
        conf.storage_server_set_url(name, url)

    # Update Defaults
    if not conf.defaults_get_storage_server():
        conf.defaults_set_storage_server(name)


### Bootstrap Functions ###

def bootstrap_new_account(country=None, state=None, locality=None, email=None,
                          account_userdata=None, account_uid=None,
                          client_userdata=None, client_uid=None,
                          ac_server_name=None,
                          conf=None, conf_path=None):

    # Normalize Args
    if not country:
        country = _DEFAULT_COUNTRY
    if not state:
        state = _DEFAULT_STATE
    if not locality:
        locality = _DEFAULT_LOCALITY

    # Setup Conf
    if not conf:
        conf = config.ClientConfig(conf_path=conf_path)

    # Get Server Name
    if not ac_server_name:
        ac_server_name = conf.defaults_get_ac_server()

    # Get UIDs
    if not account_uid:
        account_uid = conf.defaults_get_account_uid()
        if not account_uid:
            account_uid = uuid.uuid4()
    if not client_uid:
        client_uid = conf.defaults_get_client_uid()
        if not client_uid:
            client_uid = uuid.uuid4()

    # Check Existing CRT
    old_crt = conf.client_get_crt(account_uid, client_uid, ac_server_name)
    if old_crt:
        msg = "Client already configured for server {}".format(ac_server_name)
        raise Exception(msg)

    # Update Defaults
    if not conf.defaults_get_account_uid():
        conf.defaults_set_account_uid(account_uid)
    if not conf.defaults_get_client_uid():
        conf.defaults_set_client_uid(client_uid)

    # Generate and Save Key (if necessary)
    key_pem = conf.client_get_key(account_uid, client_uid)
    if not key_pem:
        key_pem = crypto.gen_key()
        conf.client_set_key(account_uid, client_uid, key_pem)

    # Generate and Save CSR
    csr_pem = crypto.gen_csr(key_pem, country, state, locality, email)
    conf.client_set_csr(account_uid, client_uid, ac_server_name, csr_pem)

    # Bootstrap Account and Save CRT
    ac_connection = accesscontrol.ACServerConnection(server_name=ac_server_name,
                                                     account_uid=account_uid,
                                                     client_uid=client_uid,
                                                     no_client_crt=True,
                                                     conf=conf)
    with ac_connection:
        bootstrap = accesscontrol.BootstrapClient(ac_connection)
        ret = bootstrap.account(account_userdata=account_userdata,
                                account_uid=account_uid,
                                client_userdata=client_userdata,
                                client_uid=client_uid,
                                client_csr=csr_pem)
    ret_account_uid, ret_client_uid, client_crt = ret
    conf.client_set_crt(account_uid, client_uid, ac_server_name, client_crt)

    # Check and Return
    assert account_uid == ret_account_uid
    assert client_uid == ret_client_uid
    return account_uid, client_uid, client_crt


### Helper Functions ###

def prep_connections(connection_type,
                     clients=None,
                     server_names=None,
                     conf=None, conf_path=None,
                     account_uid=None, client_uid=None):

    ## Arg Defaults ##
    if not server_names:
        server_names = [None]

    ## Setup Connections ##
    if clients:
        connections = [client.connection for client in clients]
    else:
        connections = []
        for server_name in server_names:
            connections.append(connection_type(server_name=server_name,
                                               conf=conf, conf_path=conf_path,
                                               account_uid=account_uid, client_uid=client_uid))
    return connections

def prep_clients(client_type, connections):

    ## Setup Clients ##
    clients = []
    for connection in connections:
        clients.append(client_type(connection))
    return clients

def open_connections(connections):
    opened = []
    for connection in connections:
        if not connection.is_open:
            connection.open()
            opened.append(connection)
    return opened

def close_connections(opened):
    for connection in opened:
        connection.close()


### Token Functions ###

def get_tokens(objtype, objperm, objuid=None,
               ac_connections=None, ac_server_names=None,
               conf=None, conf_path=None,
               account_uid=None, client_uid=None):

    ## Setup Connections ##
    if not ac_connections:
        ac_connections = prep_connections(accesscontrol.ACServerConnection,
                                          server_names=ac_server_names,
                                          conf=conf, conf_path=conf_path,
                                          account_uid=account_uid, client_uid=client_uid)

    ## Setup Clients ##
    authz_clients = prep_clients(accesscontrol.AuthorizationsClient, ac_connections)

    ## Open Connections ##
    ac_opened = open_connections(ac_connections)

    ## Get tokens ##
    tokens = {}
    errors = {}
    for authz_client in authz_clients:
        srv_name = authz_client.ac_connection.server_name
        uid = authz_client.request(objtype, objperm, objuid)
        try:
            tok = authz_client.wait_token(uid)
        except accesscontrol.AuthorizationException as err:
            errors[srv_name] = err
        else:
            tokens[srv_name] = tok

    ## Close Connections ##
    close_connections(ac_opened)

    ## Return ##
    return tokens, errors


### Verifier Functions ###

def setup_verifiers(verifier_uid=None, accounts=None, authenticators=None, tokens=None,
                    verifiers=None,
                    ac_connections=None, ac_server_names=None,
                    conf=None, conf_path=None,
                    account_uid=None, client_uid=None):

    ## Arg Defaults ##
    if not conf:
        conf = config.ClientConfig(conf_path=conf_path)
    if not account_uid:
        account_uid = conf.defaults_get_account_uid()
        if not account_uid:
            raise(ValueError("Missing Default Account UID"))
    if not verifier_uid:
        verifier_uid = uuid.uuid4()
    if not verifiers:
        # Create self-referencing verifier
        verifiers = [verifier_uid]

    ## Setup Connections ##
    if not ac_connections:
        ac_connections = prep_connections(accesscontrol.ACServerConnection,
                                          server_names=ac_server_names,
                                          conf=conf, conf_path=conf_path,
                                          account_uid=account_uid, client_uid=client_uid)

    ## Setup Clients ##
    verifier_clients = prep_clients(accesscontrol.VerifiersClient, ac_connections)

    ## Open Connections ##
    ac_opened = open_connections(ac_connections)

    # Setup Permissions
    verifiers = setup_permissions(constants.TYPE_VERIFIER, objuid=verifier_uid,
                                  verifiers=verifiers, ac_connections=ac_connections)

    ## Get Verifier Create Tokens ##
    if not tokens:
        tokens, errors = get_tokens(constants.TYPE_SRV_AC, constants.PERM_CREATE,
                                    ac_connections=ac_connections)

    ## Setup Verifiers ##
    if not accounts:
        accounts = [account_uid]
    if not authenticators:
        authenticators = []
    for client in verifier_clients:
        srv_name = client.ac_connection.server_name
        token = tokens[srv_name]
        uid = client.create([token], uid=verifier_uid,
                            accounts=accounts, authenticators=authenticators)
        assert(uid == verifier_uid)

    ## Close Connections ##
    close_connections(ac_opened)

    ## Return ##
    return [verifier_uid]

def fetch_verifiers(verifier_uid, tokens=None,
                    ac_connections=None, ac_server_names=None,
                    conf=None, conf_path=None,
                    account_uid=None, client_uid=None):

    ## Setup Connections ##
    if not ac_connections:
        ac_connections = prep_connections(accesscontrol.ACServerConnection,
                                          server_names=ac_server_names,
                                          conf=conf, conf_path=conf_path,
                                          account_uid=account_uid, client_uid=client_uid)

    ## Setup Clients ##
    verifier_clients = prep_clients(accesscontrol.VerifiersClient, ac_connections)

    ## Open Connections ##
    ac_opened = open_connections(ac_connections)

    ## Get Verifier Read Tokens ##
    if not tokens:
        tokens, errors = get_tokens(constants.TYPE_VERIFIER, constants.PERM_READ,
                                    objuid=verifier_uid,
                                    ac_connections=ac_connections)

    ## Fetch Verifiers ##
    verifiers = {}
    errors = {}
    for client in verifier_clients:
        srv_name = client.ac_connection.server_name
        token = tokens[srv_name]
        verifiers[srv_name] = client.fetch([token], verifier_uid)

    ## Close Connections ##
    close_connections(ac_opened)

    ## Return ##
    return verifiers, errors


### Permissions Functions ###

def setup_permissions(objtype, objuid=None, tokens=None,
                      verifiers=None,
                      ac_connections=None, ac_server_names=None,
                      conf=None, conf_path=None,
                      account_uid=None, client_uid=None):

    ## Setup Connections ##
    if not ac_connections:
        ac_connections = prep_connections(accesscontrol.ACServerConnection,
                                          server_names=ac_server_names,
                                          conf=conf, conf_path=conf_path,
                                          account_uid=account_uid, client_uid=client_uid)

    ## Setup Clients ##
    permissions_clients = prep_clients(accesscontrol.PermissionsClient, ac_connections)

    ## Open Connections ##
    ac_opened = open_connections(ac_connections)

    ## Setup Verifiers ##
    if not verifiers:
        verifiers = setup_verifiers(ac_connections=ac_connections)

    ## Setup Tokens ##
    if not tokens:
        tokens, errors = get_tokens(constants.TYPE_SRV_AC, constants.PERM_CREATE,
                                    ac_connections=ac_connections)

    ## Setup Permissions ##
    for client in permissions_clients:
        srv_name = client.ac_connection.server_name
        token = tokens[srv_name]
        outtype, outuid = client.create([token], objtype, objuid=objuid, v_default=verifiers)

    ## Close Connections ##
    close_connections(ac_opened)

    ## Return ##
    return verifiers


### Collection Functions ###

def setup_collection(col_uid=None, ac_server_urls=None, tokens=None,
                     verifiers=None,
                     storage_connections=None, storage_server_names=None,
                     ac_connections=None, ac_server_names=None,
                     conf=None, conf_path=None,
                     account_uid=None, client_uid=None):

    ## Setup Connections ##
    if not storage_connections:
        storage_connections = prep_connections(storage.StorageServerConnection,
                                               server_names=storage_server_names,
                                               conf=conf, conf_path=conf_path,
                                               account_uid=account_uid, client_uid=client_uid)
    if not ac_connections:
        ac_connections = prep_connections(accesscontrol.ACServerConnection,
                                          server_names=ac_server_names,
                                          conf=conf, conf_path=conf_path,
                                          account_uid=account_uid, client_uid=client_uid)

    ## Setup Clients ##
    collection_clients = prep_clients(storage.CollectionsClient, storage_connections)

    ## Open Connections ##
    storage_opened = open_connections(storage_connections)
    ac_opened = open_connections(ac_connections)

    ## Setup Collection ##

    # Setup UID
    if not col_uid:
        col_uid = uuid.uuid4()

    # Setup URLS
    ac_server_urls = []
    for ac_connection in ac_connections:
        ac_server_urls.append(ac_connection.url_srv)

    # Setup Permissions
    verifiers = setup_permissions(constants.TYPE_COL, objuid=col_uid, verifiers=verifiers,
                                  ac_connections=ac_connections)

    # Get Storage Server Create Tokens
    if not tokens:
        tokens, errors = get_tokens(constants.TYPE_SRV_STORAGE, constants.PERM_CREATE,
                                    ac_connections=ac_connections)

    # Create Collections
    for client in collection_clients:
        uid = client.create(tokens, ac_server_urls, uid=col_uid)
        assert(uid == col_uid)

    ## Close Connections ##

    ## Return ##
    return col_uid, verifiers


### Secret Functions ###

def store_secret(sec_data, sec_uid=None, tokens=None,
                 col_uid=None, verifiers=None,
                 storage_connections=None, storage_server_names=None,
                 ac_connections=None, ac_server_names=None,
                 conf=None, conf_path=None,
                 account_uid=None, client_uid=None):

    ## Setup Connections ##
    if not storage_connections:
        storage_connections = prep_connections(storage.StorageServerConnection,
                                               server_names=storage_server_names,
                                               conf=conf, conf_path=conf_path,
                                               account_uid=account_uid, client_uid=client_uid)
    if not ac_connections:
        ac_connections = prep_connections(accesscontrol.ACServerConnection,
                                          server_names=ac_server_names,
                                          conf=conf, conf_path=conf_path,
                                          account_uid=account_uid, client_uid=client_uid)

    ## Setup Clients ##
    secret_clients = prep_clients(storage.SecretsClient, storage_connections)

    ## Open Connections ##
    storage_opened = open_connections(storage_connections)
    ac_opened = open_connections(ac_connections)

    ## Setup Secret ##

    # Setup UID
    if not sec_uid:
        sec_uid = uuid.uuid4()

    # Setup Collection
    if not col_uid:
        col_uid, verifiers = setup_collection(verifiers=verifiers,
                                              storage_connections=storage_connections,
                                              ac_connections=ac_connections)

    # Get Collection Create Tokens
    if not tokens:
        tokens, errors = get_tokens(constants.TYPE_COL, constants.PERM_CREATE, objuid=col_uid,
                                    ac_connections=ac_connections)

    # Create Secret
    # Todo: shard
    for client in secret_clients:
        uid = client.create(tokens, col_uid, sec_data, uid=sec_uid)
        assert(uid == sec_uid)

    ## Close Connections ##
    close_connections(storage_opened)
    close_connections(ac_opened)

    ## Return ##
    return sec_uid, col_uid, verifiers

def fetch_secret(sec_uid, col_uid, tokens=None,
                 storage_connections=None, storage_server_names=None,
                 ac_connections=None, ac_server_names=None,
                 conf=None, conf_path=None,
                 account_uid=None, client_uid=None):

    ## Setup Connections ##
    if not storage_connections:
        storage_connections = prep_connections(storage.StorageServerConnection,
                                               server_names=storage_server_names,
                                               conf=conf, conf_path=conf_path,
                                               account_uid=account_uid, client_uid=client_uid)
    if not ac_connections:
        ac_connections = prep_connections(accesscontrol.ACServerConnection,
                                          server_names=ac_server_names,
                                          conf=conf, conf_path=conf_path,
                                          account_uid=account_uid, client_uid=client_uid)

    ## Setup Clients ##
    secret_clients = prep_clients(storage.SecretsClient, storage_connections)

    ## Open Connections ##
    storage_opened = open_connections(storage_connections)
    ac_opened = open_connections(ac_connections)

    ## Fetch Secret ##

    # Get Collection read Tokens
    if not tokens:
        tokens, errors = get_tokens(constants.TYPE_COL, constants.PERM_READ, objuid=col_uid,
                                    ac_connections=ac_connections)

    # Read Secret
    # Todo: unshard
    for client in secret_clients:
        sec = client.fetch(tokens, col_uid, sec_uid)
        sec_data = sec['data']

    ## Close Connections ##
    close_connections(storage_opened)
    close_connections(ac_opened)

    ## Return ##
    return str(sec_data)
