"""
functionality:
- handle favourite state for videos, channels and playlists
"""

from datetime import datetime

from home.src.es.connect import ElasticWrap
from home.src.ta.urlparser import Parser


class FavouriteState:
    """handle favourite status for videos"""

    def __init__(self, youtube_id, is_favourite):
        self.youtube_id = youtube_id
        self.is_favourite = is_favourite
        self.stamp = int(datetime.now().timestamp())
        self.pipeline = f"_ingest/pipeline/favourite_{youtube_id}"

    def change(self):
        """change favourite state of item(s)"""
        print(f"{self.youtube_id}: change favourite state to {self.is_favourite}")
        url_type = self._dedect_type()
        if url_type != "video":
            print(f"can only set favourite on videos")
            return

        self.change_vid_state()

    def _dedect_type(self):
        """find youtube id type"""
        url_process = Parser(self.youtube_id).parse()
        url_type = url_process[0]["type"]
        return url_type

    def change_vid_state(self):
        """change favourited state of video"""
        path = f"ta_video/_update/{self.youtube_id}"
        data = {
            "doc": {
                "is_favourite": self.is_favourite,
            }
        }
        response, status_code = ElasticWrap(path).post(data=data)
        if status_code != 200:
            print(response)
            raise ValueError("failed to mark video as watched")
