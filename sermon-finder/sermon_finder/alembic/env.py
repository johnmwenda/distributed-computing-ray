from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.schema import ForeignKeyConstraint


from sermon_finder.models.meta import Base
from sermon_finder.utils import generate_db_url

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)


# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

target_metadata = Base.metadata

def is_activity_id_fk(fkc):
    return [col.name for col in fkc.columns] == [
        'activity_id'
    ] and fkc.table.name == 'analytics'


def is_analytics_id_fk(fkc):
    return [col.name for col in fkc.columns] == [
        'analytics_id'
    ] and fkc.table.name == 'favorite'


def include_object(obj, name, type_, reflected, compare_to):
    if type_ == 'table' and (
        name.startswith('activity_')
        or name.startswith('analytics_')
        or name in ('old_analytics', 'old_activity')
    ):
        return False
    if isinstance(obj, ForeignKeyConstraint) and (
        is_activity_id_fk(obj) or is_analytics_id_fk(obj)
    ):
        return False
    return True


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    url = generate_db_url(url)
    context.configure(url=url)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    settings = config.get_section(config.config_ini_section)
    settings['sqlalchemy.url'] = generate_db_url(settings['sqlalchemy.url'])
    engine = engine_from_config(settings, prefix='sqlalchemy.')

    connection = engine.connect()
    context.configure(
        connection=connection,
        target_metadata=target_metadata
    )

    try:
        with context.begin_transaction():
            context.run_migrations()
    finally:
        connection.invalidate()
        connection.close()
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()