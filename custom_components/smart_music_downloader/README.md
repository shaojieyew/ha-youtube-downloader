# Smart Music Downloader for Home Assistant

This custom integration allows you to search for music on YouTube, download it as an MP3 to your local media folder, and play it immediately on any Home Assistant media player.

## Installation

1. Copy the `custom_components/smart_music_downloader` folder to your Home Assistant `config/custom_components/` directory.
2. Ensure you have `ffmpeg` installed on your Home Assistant host/container.
3. Restart Home Assistant.
4. Add `smart_music_downloader:` to your `configuration.yaml`.

## Usage

### Service: `smart_music_downloader.play_song`

| Field | Description | Example |
| --- | --- | --- |
| `entity_id` | Target media player. | `media_player.living_room_speaker` |
| `query` | Song name and artist. | `Bohemian Rhapsody Queen` |
| `music_dir` | Local path where music is saved. | `/media` |

### Automation Example

```yaml
action: smart_music_downloader.play_song
data:
  entity_id: media_player.living_room_speaker
  query: "Wada Kouji Butter-Fly"
```

## Features

- **Automatic Search**: Finds the best matching song on YouTube.
- **Efficient Caching**: Uses `.ytmeta` files in a hidden `.tmp` folder to map URLs to local files, preventing duplicate downloads.
- **Native Playback**: Integrated with Home Assistant's `media-source://` system for high-quality streaming.
