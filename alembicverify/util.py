# -*- coding: utf-8 -*-

from alembic import command
from alembic.config import Config
from alembic.environment import EnvironmentContext  # pylint: disable=E0401
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine


def make_alembic_config(uri, folder):
    """Create a configured :class:`alembic.config.Config` object. """
    config = Config()
    config.set_main_option("script_location", folder)
    config.set_main_option("sqlalchemy.url", uri)
    return config


def prepare_schema_from_migrations(uri, config, revision="head"):
    """Applies migrations to a database.

    :param string uri: The URI for the database.
    :param config: A :class:`alembic.config.Config` instance.
    :param revision: The revision we want to feed to the
        ``command.upgrade`` call. Normally it's either "head" or "+1".
    """
    engine = create_engine(uri)
    script = ScriptDirectory.from_config(config)
    command.upgrade(config, revision)
    return engine, script


def get_current_revision(config, engine, script):
    """Inspection helper. Get the current revision of a set of migrations. """
    return _get_revision(config, engine, script)


def get_head_revision(config, engine, script):
    """Inspection helper. Get the head revision of a set of migrations. """
    return _get_revision(config, engine, script, revision_type='head')


def get_current_revisions(config, engine, script):
    """Inspection helper. Safe for use in migration histories with branching migrations.

    :returns A list of revision hashes. The list will be length 1 if there are no branches at the current revision.
    """
    return _get_revision(config, engine, script, handle_branching_migrations=True)


def _get_revision(config, engine, script, revision_type='current', handle_branching_migrations=False):
    with engine.connect() as conn:
        with EnvironmentContext(config, script) as env_context:
            env_context.configure(conn, version_table="alembic_version")
            if revision_type == 'head':
                revision = env_context.get_head_revision()
            else:
                migration_context = env_context.get_context()
                if handle_branching_migrations:
                    revision = migration_context.get_current_heads()
                    has_multiple_heads = type(revision) != str
                    if not has_multiple_heads:
                        revision = [revision]
                else:
                    # handle_branching_migrations=False, so use the "old" alembic code path
                    revision = migration_context.get_current_revision()

    return revision
