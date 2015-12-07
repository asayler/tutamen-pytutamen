#!/usr/bin/env python3


### Imports ###

import sys
import json
import os
import uuid

import requests
import click


### Constants ###

_APP_NAME = 'tutamen-cli'
_PATH_SERVER_CONF = os.path.join(click.get_app_dir(_APP_NAME), 'servers')

_AUTHORIZATIONS_KEY = "authorizations"
_COLLECTIONS_KEY = "collections"
_SECRETS_KEY = "secrets"


### CLI Root ###

@click.group()
@click.option('--url', prompt=True, help="API URL")
@click.option('--cert', prompt=True, help="API Certificate File",
              type=click.Path(resolve_path=True, exists=True, readable=True, dir_okay=False))
@click.option('--key', prompt=True, help="API Private Key File",
              type=click.Path(resolve_path=True, exists=True, readable=True, dir_okay=False))
@click.option('--ca', default=None, help="API CA Certificate File",
              type=click.Path(resolve_path=True))
@click.pass_context
def cli(ctx, url, cert, key, ca):
    """COG CLI"""

    # Setup Context
    ctx.obj = {}
    ctx.obj['url'] = url
    ctx.obj['path_cert'] = cert
    ctx.obj['path_key'] = key
    ctx.obj['path_ca'] = ca


### Collection Storage Commands ###

@cli.group(name=_COLLECTIONS_KEY)
@click.pass_obj
def collections(obj):
    pass

@collections.command(name='create')
@click.argument('metadata', type=click.STRING)
@click.pass_obj
def collections_create(obj, metadata):

    url = "{}/{}/".format(obj['url'], _COLLECTIONS_KEY)
    json_out = {'metadata': metadata}
    res = requests.post(url, json=json_out, verify=obj['path_ca'],
                        cert=(obj['path_cert'], obj['path_key']))
    res.raise_for_status()
    click.echo(res.json())

### Secret Storage Commands ###

@cli.group(name=_SECRETS_KEY)
@click.pass_obj
def secrets(obj):
    pass

@secrets.command(name='data')
@click.argument('col_uid', type=click.UUID)
@click.argument('sec_uid', type=click.UUID)
@click.pass_obj
def secrets_get_data(obj, col_uid, sec_uid):

    url = "{}/{}/{}/{}/{}/versions/latest/".format(obj['url'], _COLLECTIONS_KEY, str(col_uid),
                                                   _SECRETS_KEY, str(sec_uid))
    res = requests.get(url, verify=obj['path_ca'],
                       cert=(obj['path_cert'], obj['path_key']))
    res.raise_for_status()
    click.echo(res.json())

@secrets.command(name='create')
@click.argument('col_uid', type=click.UUID)
@click.argument('data', type=click.STRING)
@click.argument('metadata', type=click.STRING)
@click.pass_obj
def secrets_create(obj, col_uid, data, metadata):

    url = "{}/{}/{}/{}/".format(obj['url'], _COLLECTIONS_KEY, str(col_uid), _SECRETS_KEY)
    json_out = {'data': data, 'metadata': metadata}
    res = requests.post(url, json=json_out, verify=obj['path_ca'],
                        cert=(obj['path_cert'], obj['path_key']))
    res.raise_for_status()
    click.echo(res.json())


### Main ###

if __name__ == '__main__':
    sys.exit(cli())
