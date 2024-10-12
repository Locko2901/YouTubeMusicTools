import traceback
import googleapiclient
from googleapiclient import discovery

def get_youtube_service(api_key):
    """Create and return a YouTube service client."""
    try:
        discovery_url = 'https://www.googleapis.com/discovery/v1/apis/youtube/v3/rest'
        service = discovery.build('youtube', 'v3', developerKey=api_key, discoveryServiceUrl=discovery_url)
        return service
    except googleapiclient.errors.UnknownApiNameOrVersion as e:
        error_message = f"Error occurred while building YouTube service client: {e.__class__.__name__}: {e}"
        detailed_traceback = traceback.format_exc()
        print(error_message)
        print(detailed_traceback)
        raise
    except Exception as e:
        error_message = f"Error occurred while building YouTube service client: {e.__class__.__name__}: {e}"
        detailed_traceback = traceback.format_exc()
        print(error_message)
        print(detailed_traceback)
        raise

def get_playlist_name(api_key, playlist_id):
    """Fetch the name of a YouTube playlist given its ID."""
    try:
        youtube = get_youtube_service(api_key)
        request = youtube.playlists().list(part='snippet', id=playlist_id)
        response = request.execute()
        
        if response['items']:
            return response['items'][0]['snippet']['title']
        else:
            return None
    except Exception as e:
        error_message = f"An error occurred while fetching the playlist name: {e.__class__.__name__}: {e}"
        detailed_traceback = traceback.format_exc()
        print(error_message)
        print(detailed_traceback)
        raise

def get_playlist_items(api_key, playlist_id):
    """Fetch the items (videos) from a YouTube playlist."""
    try:
        youtube = get_youtube_service(api_key)
        request = youtube.playlistItems().list(part='snippet', playlistId=playlist_id, maxResults=50)
        response = request.execute()

        videos = []

        while response:
            for item in response.get('items', []):
                title = item['snippet']['title']
                artist = item['snippet'].get('videoOwnerChannelTitle', 'Unknown Artist')
                video_id = item['snippet']['resourceId'].get('videoId')
                
                if video_id:
                    videos.append((title, artist, video_id))

            if 'nextPageToken' in response:
                request = youtube.playlistItems().list(
                    part='snippet',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=response['nextPageToken']
                )
                response = request.execute()
            else:
                break

        return videos if videos else None
    except Exception as e:
        print(f"An error occurred while fetching the playlist items: {e}")
        return None