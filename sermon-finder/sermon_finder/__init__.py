import datetime
from functools import partial
import logging
import random
import time
from typing import Any, Dict, Tuple, Type

import click
from pydantic import computed_field
import ray
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource
from pydantic.fields import FieldInfo
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from .remotes import FacebookDownloader
from .actor import SermonActorPool, remotecaller, ErrorResult
from .utils import generate_db_url
from .models import SermonDownloadProgress


# class AccessTokenSetting(PydanticBaseSettingsSource):
#     def get_field_value(
#         self, field: FieldInfo, field_name: str
#     ) -> Tuple[Any, str, bool]: ...

#     def __call__(self) -> Dict[str, Any]:
#         # Retrieve the aggregated settings from previous sources
#         current_state = self.current_state
#         user_id = current_state.get('
#                                     ')
#         user_token = current_state.get('user_token')
#         page_id = current_state.get('page_id')

#         import pdb; pdb.set_trace()
        
#         import requests
#         import json

#         try:
#             URL = f"https://graph.facebook.com/{user_id}/accounts"
#             # Make the GET request
#             response = requests.get(URL, params={'access_token': user_token})
#             # Print the response status code and content
#             import pdb; pdb.set_trace()
#             resp = json.loads(response.text)
#             for token_detail in resp["data"]:
#                 if token_detail['id'] == page_id:
#                     return {
#                         'access_token': token_detail['access_token']
#                     }
#             else:
#                 print("Could not get access token")
#                 raise("Could not get access token")
#         except Exception as exc:
#             print(exc)
#             raise exc


class FacebookDownloadJobSettings(BaseSettings):
    """Settings for facebook api"""

    page_id: str = '595205407650966'
    app_id: str = '1597712757718520'
    app_secret: str = '6839582841867cc3d8b2b0d13aacbe7d'
    user_id: str = '10229427195778063'
    # user_token expires in 3 months
    user_token: str = 'EAAWtHH1gffgBOZBYmvEJ0Kocmyxme8lckZBoUsilF9atmb2UC4hbdveuKVJZAhsfM2VqvetJIZCxezZBRJHZCO0qu4p8QKw21T3rR7c3FllVRUnm4nRtKM1JafcbqnCkerIfoyKIEoXXZBVzrNtP2vjgXCqWNfZBUBtWKEuQ7JbVFRDZAFLYSmAHZCJmoZD'


    @computed_field
    @property
    def access_token(self) -> dict:
        """ Return updated API header (added serviceApiKey secret).

        :return: Updated API header.
        """
        import requests
        import json

        try:
            URL = f"https://graph.facebook.com/{self.user_id}/accounts"
            # Make the GET request
            response = requests.get(URL, params={'access_token': self.user_token})
            # Print the response status code and content
            resp = json.loads(response.text)
            for token_detail in resp["data"]:
                if token_detail['id'] == self.page_id:
                    return token_detail['access_token']
            else:
                print("Could not get access token")
                raise("Could not get access token")
        except Exception as exc:
            print(exc)
            raise exc


                
    # @classmethod
    # def settings_customise_sources(
    #     cls,
    #     settings_cls: Type[BaseSettings],
    #     init_settings: PydanticBaseSettingsSource,
    #     env_settings: PydanticBaseSettingsSource,
    #     dotenv_settings: PydanticBaseSettingsSource,
    #     file_secret_settings: PydanticBaseSettingsSource,
    # ) -> Tuple[PydanticBaseSettingsSource, ...]:
    #     return (
    #         init_settings,
    #         dotenv_settings,
    #         env_settings,
    #         file_secret_settings,
    #         AccessTokenSetting(settings_cls),
    #         )



# an Engine, which the Session will use for connection
# resources
engine = create_engine(generate_db_url())
Session = sessionmaker(engine)
settings = FacebookDownloadJobSettings()

print(settings.access_token)

# with Session() as session: 
#     # new_sermon = SermonDownloadProgress(
#     #     title = "New Sermon",
#     #     description = "New Description",
#     #     processed = True,
#     #     video_created_date = datetime.datetime.now(),
#     #     english_caption_uri = "https://fb/uri/23"
#     # )
#     # session.add(new_sermon)
#     # session.commit()

#     q = select(SermonDownloadProgress)
#     data = session.scalars(q).all()
#     print(data)

#     for obj in data:
#         session.delete(obj)
#     session.flush()
#     session.commit()

# exit()

def ray_with_workflow_pkg(ray_address=None, runtime_branch=None, workflow_pkg=None):
    return ray.init(address=ray_address)


@click.group()
@click.option(
    '--runtime-branch',
    default=None,
    help="Branch to use to install runtime if running in anyscale; will use current branch if unspecified",
    metavar='BRANCH',
)
@click.option(
    '--ray-address',
    default=None,
    help="Ray address cluster to connect",
    metavar='RAY_ADDRESS',
)
@click.pass_context
def sermon_finder(click_ctx, ray_address, runtime_branch):
    """Control script for sermon-finder workflow package.

    Use RAY_ADDRESS environment variable to connect to a remote cluster;
    otherwise will use default local cluster.
    """

    click_ctx.ray = partial(
        ray_with_workflow_pkg, ray_address=ray_address, runtime_branch=runtime_branch, workflow_pkg='sermon-finder'
    )


@sermon_finder.command()
@click.pass_context
def print_sermons_progress(click_ctx):
    with Session() as session: 
        q = select(SermonDownloadProgress)
        data = session.scalars(q).all()
        print(data)


@sermon_finder.command()
@click.pass_context
def run(click_ctx):
    """Sample command that initializes ray.

    You'll want to rename & replace this with an actual command that does something useful.
    """

    with click_ctx.parent.ray():
        # call remotes and perfrom work
        matcher_pool = SermonActorPool.with_actors(FacebookDownloader.remote, 10)

        with open('log2.txt', 'w') as f:
            f.write("hala")
        
        links = [[1, 120], [2, 120], [3, 120], [4, 120], [5, 120], [6, 120], [7, 120], [8, 120], [9, 120], [10, 120]]
        start_time = time.time()
        print(f"start time {start_time}")
        for i, result in enumerate(
            matcher_pool.map_unordered_with_error(
                remotecaller(FacebookDownloader.fetch_facebook_video_links), links
            )
        ):
            print(i, result)
            # pass
        end_time = time.time()
        print(f"end time {time.time()}")
        print(f"total time {end_time - start_time}")


if __name__ == '__main__':
    ENV_VARIABLES = 
    runtime_env = {
        "env_vars": ENV_VARIABLES
    }
    ray.init(runtime_env=)
    sermon_finder()
