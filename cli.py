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


### Secret Storage Commands ###

@cli.group(name='secrets')
@click.pass_obj
def secret(obj):
    pass

@secret.command(name='get')
@click.argument('uid', type=click.UUID)
@click.pass_obj
def secret_get(obj, uid):

    url = "{}/secrets/{}/".format(obj['url'], str(uid))
    res = requests.get(url, verify=obj['path_ca'],
                       cert=(obj['path_cert'], obj['path_key']))
    res.raise_for_status()
    click.echo(res.json()['data'])

@secret.command(name='create')
@click.argument('data', type=click.STRING)
@click.pass_obj
def secret_create(obj, data):

    url = "{}/secrets/".format(obj['url'])
    jsn = {'data': data}
    click.echo(jsn)
    res = requests.post(url, json=jsn, verify=obj['path_ca'],
                        cert=(obj['path_cert'], obj['path_key']))
    res.raise_for_status()
    click.echo(res.json()['secrets'][0])


### Main ###

if __name__ == '__main__':
    sys.exit(cli())
