"""
functionality:
- handle favourite state for videos, channels and playlists
"""

from datetime import datetime

from home.src.es.connect import ElasticWrap
from home.src.ta.urlparser import Parser


class FavouriteState:
    """handle favourite checkbox for videos and channels"""

    def __init__(self, youtube_id, is_favourite):
        self.youtube_id = youtube_id
        self.is_favourite = is_favourite
        self.stamp = int(datetime.now().timestamp())
        self.pipeline = f"_ingest/pipeline/favourite_{youtube_id}"

    def change(self):
        """change favourite state of item(s)"""
        print(f"{self.youtube_id}: change favourite state to {self.is_favourite}")
        url_type = self._dedect_type()
        if url_type == "video":
            self.change_vid_state()
            return

        self._add_pipeline()
        path = f"ta_video/_update_by_query?pipeline=favourite_{self.youtube_id}"
        data = self._build_update_data(url_type)
        _, _ = ElasticWrap(path).post(data)
        self._delete_pipeline()

    def _dedect_type(self):
        """find youtube id type"""
        url_process = Parser(self.youtube_id).parse()
        url_type = url_process[0]["type"]
        return url_type

    def _build_update_data(self, url_type):
        """build update by query data based on url_type"""
        term_key_map = {
            "channel": "channel.channel_id",
            "playlist": "playlist.keyword",
        }
        term_key = term_key_map.get(url_type)

        return {
            "query": {
                "bool": {
                    "must": [
                        {"term": {term_key: {"value": self.youtube_id}}},
                        {
                            "term": {
                                "favourite": {
                                    "value": not self.is_favourite
                                }
                            }
                        },
                    ],
                }
            }
        }

    def _add_pipeline(self):
        """add ingest pipeline"""
        data = {
            "description": f"{self.youtube_id}: favourite {self.is_favourite}",
            "processors": [
                {
                    "set": {
                        "field": "favourite",
                        "value": self.is_favourite,
                    }
                },
                {
                    "set": {
                        "field": "favourite_date",
                        "value": self.stamp,
                    }
                },
            ],
        }
        _, _ = ElasticWrap(self.pipeline).put(data)

    def _delete_pipeline(self):
        """delete pipeline"""
        ElasticWrap(self.pipeline).delete()
