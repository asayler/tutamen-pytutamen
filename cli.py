#!/usr/bin/env python3


### Imports ###

import sys
import os

import click

import client

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

    # Setup Client
    c = client.Client(url_server=url, path_ca=ca, path_cert=cert, path_key=key)
    c.open()
    ctx.call_on_close(c.close)

    # Setup Context
    ctx.obj = {}
    ctx.obj['client'] = c

### Collection Storage Commands ###

@cli.group(name='collections')
@click.pass_obj
def collections(obj):

    obj['collections_client'] = client.CollectionsClient(obj['client'])

@collections.command(name='create')
@click.option('--metadata', default={}, type=click.STRING)
@click.pass_obj
def collections_create(obj, metadata):

    click.echo(obj['collections_client'].create(metadata=metadata))

### Secret Storage Commands ###

@cli.group(name='secrets')
@click.pass_obj
def secrets(obj):

    obj['secrets_client'] = client.SecretsClient(obj['client'])

@secrets.command(name='data')
@click.argument('col_uid', type=click.UUID)
@click.argument('sec_uid', type=click.UUID)
@click.pass_obj
def secrets_get_data(obj, col_uid, sec_uid):

    click.echo(obj['secrets_client'].data(col_uid, sec_uid))

@secrets.command(name='create')
@click.argument('col_uid', type=click.UUID)
@click.argument('data', type=click.STRING)
@click.option('--metadata', default={}, type=click.STRING)
@click.pass_obj
def secrets_create(obj, col_uid, data, metadata):

    click.echo(obj['secrets_client'].create(col_uid, data, metadata=metadata))

### Main ###

if __name__ == '__main__':
    sys.exit(cli())
