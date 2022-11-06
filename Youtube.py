from youtube_search import YoutubeSearch

class Download:
    def name(self):
        results = YoutubeSearch('search terms', max_results=10)
        return results

if __name__ == __main__