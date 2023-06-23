class video_data(object):
    
    def __init__(self, title: str = None, image_url: str = None, yt_dlp_dict: dict = None):
        if image_url is not None:
            self.thumbnail_url = image_url
        else:
            self.thumbnail_url = None
        
        if title is not None:
            self.title = title
        else:
            self.title = None
        
        if yt_dlp_dict is not None:
            video_info = yt_dlp_dict['entries'][0]
            self.title = video_info['title']
            self.thumbnail_url = video_info['thumbnail']   

    def has_data(self) -> bool:
        if (self.thumbnail_url is None) and (self.title is None):
            return False
        return True
    
    def set_title(self, title: str) -> None:
        self.title = title

    def set_thumbnail_url(self, url: str) -> None:
        self.thumbnail_url = url

    def set_yt_dlp_dict(self, yt_dlp_dict: dict) -> None:
        video_info = yt_dlp_dict['entries'][0]
        self.title = video_info['title']
        self.thumbnail_url = video_info['thumbnail']

class video_data_guild:
    def __init__(self) -> None:
        self.video_dict = {
            int : video_data
        }
    
    def set_video_data(self, guild_id: int, video_data: video_data) -> None:
        self.video_dict[guild_id] = video_data
    
    def get_video_data(self, guild_id: int) -> video_data:
        return self.video_dict.get(guild_id, video_data())
