"""The Smart Music Downloader integration."""
import os
import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, SERVICE_PLAY_SONG, DEFAULT_MUSIC_DIR
from .downloader import async_search_and_download, async_get_music_list

_LOGGER = logging.getLogger(__name__)

SERVICE_PLAY_SONG_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("query"): cv.string,
    vol.Optional("music_dir", default=DEFAULT_MUSIC_DIR): cv.string,
})

SERVICE_LIST_SONGS_SCHEMA = vol.Schema({
    vol.Optional("music_dir", default=DEFAULT_MUSIC_DIR): cv.string,
})

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Smart Music Downloader integration."""
    
    async def handle_play_song(call: ServiceCall):
        # ... existing code ...
        entity_id = call.data.get("entity_id")
        query = call.data.get("query")
        music_dir = call.data.get("music_dir", DEFAULT_MUSIC_DIR)

        _LOGGER.info("Smart Music Downloader: Request to play '%s' on %s", query, entity_id)

        # 1. Search and Download
        mp3_path = await async_search_and_download(hass, query, music_dir)
        
        if not mp3_path:
            _LOGGER.error("Smart Music Downloader: Failed to find or download '%s'", query)
            return

        # 2. Convert to media-source URI
        rel_path = os.path.relpath(mp3_path, music_dir)
        ha_path = rel_path.replace("\\", "/")
        media_content_id = f"media-source://media_source/local/{ha_path}"

        _LOGGER.info("Smart Music Downloader: Triggering playback for %s", media_content_id)

        # 3. Call media_player.play_media
        await hass.services.async_call(
            "media_player",
            "play_media",
            {
                "entity_id": entity_id,
                "media_content_id": media_content_id,
                "media_content_type": "audio/mpeg",
            },
            blocking=True,
        )

    async def handle_list_songs(call: ServiceCall):
        """Handle the list_songs service call."""
        music_dir = call.data.get("music_dir", DEFAULT_MUSIC_DIR)
        songs = await async_get_music_list(hass, music_dir)
        return {"songs": songs}

    hass.services.async_register(
        DOMAIN, SERVICE_PLAY_SONG, handle_play_song, schema=SERVICE_PLAY_SONG_SCHEMA
    )

    hass.services.async_register(
        DOMAIN, 
        "list_songs", 
        handle_list_songs, 
        schema=SERVICE_LIST_SONGS_SCHEMA,
        supports_response=vol.Maybe(vol.Coerce(str)) # To support returning data
    )

    return True

