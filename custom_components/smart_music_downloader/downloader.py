import os
import re
import json
import logging
import asyncio
import yt_dlp
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

def get_video_id(url):
    """Extracts the video ID from a YouTube URL."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/|v\/|youtu.be\/)([0-9A-Za-z_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_meta_file_path(target_dir, video_id):
    """Returns the path to the .ytmeta file, creating .tmp if needed."""
    tmp_dir = os.path.join(target_dir, ".tmp")
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    return os.path.join(tmp_dir, f"{video_id}.ytmeta")

def check_meta_cache(target_dir, video_id):
    """Checks if a video has already been downloaded based on its metadata file."""
    meta_path = get_meta_file_path(target_dir, video_id)
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                mp3_path = content.get('mp3_path')
                if mp3_path and os.path.exists(mp3_path):
                    _LOGGER.info("Cache Hit for %s: %s", video_id, os.path.basename(mp3_path))
                    return mp3_path
        except Exception as e:
            _LOGGER.error("Failed to read meta file %s: %s", meta_path, e)
    return None

def verify_is_song(info):
    """
    Verifies if the video is likely a song based on metadata.
    Includes strict blacklisting for dramas, shorts, and long-form content.
    """
    title = info.get('title', '').lower()
    uploader = info.get('uploader', '').lower()
    duration = info.get('duration', 0)
    
    # 1. Duration check (songs are rarely > 15 mins, unless they are mixes)
    if duration > 420: # 15 minutes
        if 'mix' not in title and 'album' not in title:
            return False

    # 2. Blacklist: Keywords that indicate non-music content
    blacklist = {
        'drama', 'shortplay', 'episode', 'ep.', 'full movie', 'preview', 
        'trailer', 'teaser', 'reaction', 'vlog', 'gameplay', 'walkthrough',
        'tutorial', 'highlights', 'news', 'interview', 'compilation'
    }
    if any(word in title for word in blacklist):
        # Allow if it's an "OST" or "Theme" despite the keyword
        if 'ost' not in title and 'theme' not in title and 'song' not in title:
            return False

    # 3. Whitelist: Metadata that strongly indicates music
    if info.get('track') or info.get('artist') or info.get('album'):
        return True
    
    categories = info.get('categories', [])
    if 'Music' in categories:
        return True
        
    tags = [t.lower() for t in info.get('tags', [])] if info.get('tags') else []
    music_tags = {'music', 'song', 'audio', 'soundtrack', 'ost', 'lyrics'}
    if any(tag in music_tags for tag in tags):
        return True
        
    if uploader.endswith(' - topic'):
        return True

    # 4. Keyword Check: Common music indicators in title
    music_indicators = ['official audio', 'official lyric video', 'official music video', 'mv', 'cover']
    if any(ind in title for ind in music_indicators):
        return True

    return False


def find_existing_song(query: str, download_dir: str):
    """Checks if a similar song already exists in the download_dir."""
    def get_keywords(s):
        keywords = set(re.findall(r'[\w\d]+', s.lower()))
        if len(keywords) > 1:
            keywords = {k for k in keywords if len(k) > 1}
        return keywords

    query_keywords = get_keywords(query)
    if not query_keywords or not os.path.exists(download_dir):
        return None

    for filename in os.listdir(download_dir):
        if filename.lower().endswith(".mp3"):
            file_keywords = get_keywords(os.path.splitext(filename)[0])
            if not file_keywords:
                continue
            if query_keywords.issubset(file_keywords) or file_keywords.issubset(query_keywords):
                return os.path.join(download_dir, filename)
            intersection = query_keywords.intersection(file_keywords)
            if len(intersection) >= min(len(query_keywords), len(file_keywords)) * 0.8:
                return os.path.join(download_dir, filename)
    return None

class YDLogger:
    """yt-dlp logger adapter for HA."""
    def debug(self, msg): pass
    def info(self, msg): _LOGGER.info("yt-dlp: %s", msg)
    def warning(self, msg): _LOGGER.warning("yt-dlp: %s", msg)
    def error(self, msg): _LOGGER.error("yt-dlp: %s", msg)

async def async_download_youtube_audio(hass: HomeAssistant, url: str, target_dir: str):
    """Downloads audio from YouTube."""
    video_id = get_video_id(url)
    if not video_id:
        return None

    cached_path = await hass.async_add_executor_job(check_meta_cache, target_dir, video_id)
    if cached_path:
        return cached_path

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(target_dir, '%(artist)s - %(title)s.%(ext)s'),
        'quiet': True,
        'logger': YDLogger(),
        'noprogress': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['dash', 'hls']
            }
        }
    }


    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_path = f"{os.path.splitext(filename)[0]}.mp3"
            
            # Create meta file
            meta_path = get_meta_file_path(target_dir, video_id)
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump({'url': url, 'mp3_path': os.path.abspath(mp3_path), 'title': info.get('title')}, f, indent=2)
            return mp3_path

    return await hass.async_add_executor_job(_download)

async def async_search_and_download(hass: HomeAssistant, query: str, target_dir: str):
    """Searches and downloads a song."""
    existing = await hass.async_add_executor_job(find_existing_song, query, target_dir)
    if existing:
        return existing

    ydl_opts = {'quiet': True, 'logger': YDLogger(), 'noprogress': True}
    
    def _search():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch5:{query}", download=False)
            if not results or 'entries' not in results:
                return None
            
            for entry in results['entries']:
                if not entry: continue
                # Check cache for each search result
                video_id = entry.get('id')
                cached = check_meta_cache(target_dir, video_id)
                if cached: return entry['webpage_url']
                
                # Check fuzzy match for search result
                fuzzy = find_existing_song(entry.get('title', ''), target_dir)
                if fuzzy: return entry['webpage_url']
                
                if verify_is_song(entry):
                    return entry['webpage_url']
            
            return results['entries'][0]['webpage_url'] if results['entries'] else None

    url = await hass.async_add_executor_job(_search)
    if url:
        return await async_download_youtube_audio(hass, url, target_dir)
    return None
