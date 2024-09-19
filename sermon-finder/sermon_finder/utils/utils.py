import collections
from functools import wraps
import os

from sqlalchemy import select
from sermon_finder.models.db import SermonDownloadProgress

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # This is your Project Root

class GeneratorCloseReturn(collections.abc.Generator):
    """Preserve the return value of ``generator`` and return as value of close().

    Back-port of `new functionality <https://discuss.python.org/t/let-generator-close-return-stopiteration-value/24786/25>`_
    from Python 3.13.
    """

    def __init__(self, generator):
        self.generator = generator
        self.close_value = None

    def __next__(self):
        try:
            return next(self.generator)
        except StopIteration as si:
            self.close_value = si.value
            raise

    def send(self, value):
        try:
            return self.generator.send(value)
        except StopIteration as si:
            self.close_value = si.value
            raise

    def throw(self, *args, **kwargs):
        try:
            return self.generator.throw(*args, **kwargs)
        except StopIteration as si:
            self.close_value = si.value
            raise

    def close(self):
        return self.close_value


def generator_close_return(gen_fn):
    """Decorator to ensure a generator function always provides its return value on ``.close()``."""

    @wraps(gen_fn)
    def _gcr(*args, **kwargs):
        return GeneratorCloseReturn(gen_fn(*args, **kwargs))

    return _gcr


def generate_db_url(url=None):
    import os

    if url:
        return url.replace('////', f'////{os.environ["HOME"]}/')
    else:
        try:
            from configparser import ConfigParser
        except ImportError:
            from configparser import ConfigParser  # ver. < 3.0

        # instantiate
        config = ConfigParser()

        # parse existing file
        config.read(f'{ROOT_DIR}/alembic.ini')
        url = config['alembic']['sqlalchemy.url']
        if 'sqlite' in url:
            return generate_db_url(url)
        else:
            raise Exception("Cannot find database url")


def get_recent_facebook_video() -> SermonDownloadProgress | None:
    from sermon_finder import Session

    with Session() as session: 
        q = select(SermonDownloadProgress).order_by(SermonDownloadProgress.created_date.desc).limit(1)
        data = session.scalars(q).all()
        return data