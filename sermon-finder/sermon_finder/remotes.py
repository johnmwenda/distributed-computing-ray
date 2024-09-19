import asyncio
import datetime
import random
import time
from urllib.parse import urlparse, parse_qs

import ray
from sqlalchemy import select
from pyfacebook import FacebookApi, VideosResponse


class FetchVideos:
    PAGE_ID = None
    PATH = None

    def __init__(self, api_client, page_id, app_id, app_secret, access_token, since, until, count=10):
        self.PAGE_ID = page_id
        self.PATH = f"{page_id}/videos"
        self.since = since
        self.until = until
        self.count = count
        self.paged_results = []

        self.api = api_client

    def get_query_params(self, url):
        # Parse the URL
        parsed_url = urlparse(url)
        # Extract the query component
        query_string = parsed_url.query
        # Convert the query parameters to a dictionary
        query_params = parse_qs(query_string)
        # Convert list values to single values if only one value is present
        query_params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}
        return query_params

    def get_videos_response(self) -> VideosResponse:
        query_params = {
            'fields': 'id,created_time,description,title,published,length,permalink_url,updated_time',
            'since': self.since,
            'until': self.until,
            'limit': self.count,
            'access_token': ACCESS_TOKEN,
            'limit': self.count
        }
        return api.get(self.PATH, args=query_params)

    def get_all_paged_results(self, url) -> list:
        """Recursive function to get all paged video results"""
        resp = api.get(self.PATH, args={**self.get_query_params(url), 'count': self.count})
        self.paged_results.extend(resp['data'])

        if resp['paging'].get('next'):
            return self.get_all_paged_results(resp['paging'].get('next'))
        else:
            return self.paged_results

    def get_videos(self):
        initial_data = self.get_videos_response()
        videos_list = initial_data['data'] 
        paging = initial_data['paging']
        
        if paging['next']:
            print("fetch length", len(videos_list), 'next', paging['next'])
            all_paged_results = self.get_all_paged_results(paging['next'])
            videos_list.extend(all_paged_results)

        return 
    



@ray.remote
class FacebookDownloader:
    settings: None

    def find_new_sermons():
        # checks Facebook for latest sermons
        vid_resp = FetchVideos(PAGE_ID, since='2020-01-01', until='2024-12-31', count=20)
        data = vid_resp.get_videos()



    def process_videos(self, durations):
        from sermon_finder import Session, settings
        from sermon_finder.models import SermonDownloadProgress

        self.settings = settings

        # fetches facebook video duration not yet processed
        # 1. check whether new facebook video is posted 
        #   - probably use S3 to store and update the CSV list
        # 1. fetch list of all new live videos
        # 2. update postgres database
        id = random.randint(13, 2123123)

        async def main():
            async def run(duration):
                print(f"ID: {id} working on duration {duration}")

                with Session() as session:
                    new_sermon = SermonDownloadProgress(
                        title = f"New Sermon {id} + {duration}",
                        description = f"New Description {id} + {duration}",
                        processed = True,
                        video_created_date = datetime.datetime.now(),
                        english_caption_uri = f"https://fb/uri/23/{id}+{duration}"
                    )
                    session.add(new_sermon)
                    session.commit()

            await asyncio.gather(*[run(duration) for duration in durations])

        loop = asyncio.get_event_loop()

        try:

            print(f'ID: {id} loop running')

            loop.run_until_complete(main())
        except Exception as e:
            raise e
        finally:
            loop.close()
        # print([link for link in duration])
        # time.sleep(duration)
        
        return f"completed working on {durations}"
