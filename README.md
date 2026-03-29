# Home Assistant YouTube Downloader 🎵

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A powerful Home Assistant integration that allows you to search for any song on YouTube, download it as a high-quality MP3 to your local media folder, and play it immediately on any media player.

## ✨ Features

- **Search by Name**: No need for URLs. Just say "Bohemian Rhapsody" or "姚曉棠 - 看著我的眼睛說".
- **Intelligent Caching**: Uses `.ytmeta` files in a hidden `.tmp` folder to map YouTube IDs to local files.
- **Fast Playback**: Skips searching and downloading if the song already exists locally.
- **Native Integration**: Uses Home Assistant's `media-source://` URI system for reliable local playback.
- **Automatic Conversion**: Fetches the best audio stream and converts it to MP3 (192kbps).

## 🚀 Installation

### Manual Installation
1. Copy the `custom_components/smart_music_downloader` folder into your Home Assistant `config/custom_components/` directory.
2. Ensure `ffmpeg` is installed on your host (included by default in HA OS and Official Docker).
3. Restart Home Assistant.
4. Add `smart_music_downloader:` to your `configuration.yaml`.

## 🛠 Usage

### Service: `smart_music_downloader.play_song`

| Field | Description | Example |
| --- | --- | --- |
| `entity_id` | **Required**. Target media player. | `media_player.living_room_speaker` |
| `query` | **Required**. Song name and/or artist. | `Rick Astley Never Gonna Give You Up` |
| `music_dir` | *Optional*. Local path where music is saved (defaults to `/media`). | `/media` |

### Automation Example
```yaml
alias: Play morning music
trigger:
  - platform: time
    at: "07:00:00"
action:
  - service: smart_music_downloader.play_song
    data:
      entity_id: media_player.master_bedroom_speaker
      query: "Lofi hip hop mix"
```

## 📂 File Structure
- Music is saved as: `[Artist - Song].mp3`
- Cache is saved in: `.tmp/[video_id].ytmeta`
