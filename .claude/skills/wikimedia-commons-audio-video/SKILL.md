---
name: wikimedia-commons-audio-video
description: Work with audio and video files on Wikimedia Commons — format policies and patent restrictions, uploading and transcoding with video2commons, metadata via the Action API (duration, sample rate, codecs, resolution), keyframe thumbnails for video, the TimedMediaHandler player widget, TimedText subtitles, the transcoding pipeline, and creating derivative clips from existing media
depends_on: [wikimedia-api-access, wikimedia-commons, wikimedia-commons-thumbnails]
license: MIT
compatibility: opencode
skill_discovery_hints:
  - keywords: ["audio", "video", "multimedia", "OGG", "Ogg", "WebM", "VP9", "VP8", "AV1", "Opus", "Vorbis", "FLAC", "Theora"]
  - keywords: ["transcode", "transcoding", "video2commons", "format conversion", "codec", "convert video", "convert audio"]
  - keywords: ["TimedText", "subtitles", "captions", ".srt", "SRT", "TimedMediaHandler", "closed caption"]
  - keywords: ["player widget", "media player", "embed video", "playback", "keyframe", "video thumbnail", "audio thumbnail"]
  - keywords: ["mediatype", "playtime_seconds", "playtime_string", "sample rate", "resolution", "duration", "bitrate"]
  - keywords: ["patent", "MP4", "H.264", "H.265", "free codec", "royalty-free", "MPEG LA"]
  - keywords: ["Commons audio", "Commons video", "upload audio", "upload video", "media file Commons"]
  - keywords: ["ffmpeg", "Commons ffmpeg", "convert WebM", "video editing Commons"]
last_verified: 2026-06-16
---

> ⚠️ **User-Agent required:** All curl and code examples in this skill access Wikimedia APIs. Requests without a descriptive `User-Agent` header will be blocked with HTTP 403 or 429. See the **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** skill for the correct format and rate-limiting patterns.

---

## 1. Audio File Types and Format Policy

### Allowed Audio Formats

| Format | Extension | Codec(s) | Notes |
|--------|-----------|----------|-------|
| **Ogg** | `.ogg`, `.oga` | Vorbis, Opus, FLAC | Preferred format. Patent-free |
| **FLAC** | `.flac` | FLAC (lossless) | Lossless audio. Large files |
| **WAV** | `.wav` | PCM (uncompressed) | Uncompressed. Very large files |
| **MP3** | `.mp3` | MPEG Audio Layer 3 | **Accepted but discouraged.** Patent-encumbered (though most patents have expired). Prefer Ogg Vorbis or Opus for new uploads |

### Blocked Audio Formats

| Format | Reason |
|--------|--------|
| **MP2, AAC** | Software patent restrictions |
| **WMA** | Proprietary Microsoft format |
| **Any DRM-protected** | Conflicts with free licensing requirements |

### Why Ogg/Opus Is Preferred

The Wikimedia Foundation advocates for **free, unencumbered codecs**:

- **Vorbis**: Mature, widely supported, open standard
- **Opus**: Modern, better quality at lower bitrates, IETF standard (RFC 6716). **Preferred for new uploads**
- **FLAC**: Lossless. Best for archival-quality audio where file size isn't the primary concern

### Conversion Patterns (ffmpeg)

```bash
# Convert MP3/WAV to Ogg Vorbis
ffmpeg -i input.mp3 -c:a libvorbis -q:a 5 output.ogg

# Convert to Opus (preferred)
ffmpeg -i input.mp3 -c:a libopus -b:a 96k output.ogg

# Convert FLAC to Ogg Vorbis (for smaller streaming version)
ffmpeg -i input.flac -c:a libvorbis -q:a 8 output.ogg
```

---

## 2. Video File Types and Format Policy

### Allowed Video Formats

| Format | Extension | Codec(s) | Notes |
|--------|-----------|----------|-------|
| **WebM** | `.webm` | VP8, VP9, AV1 | **Preferred format.** Patent-free |
| **Ogg** | `.ogv` | Theora | Older standard. Still accepted |

### Blocked Video Formats

| Format | Reason |
|--------|--------|
| **MP4 / H.264** | Software patent restrictions (MPEG LA licensing) |
| **H.265 / HEVC** | Software patent restrictions — even more restrictive than H.264 |
| **AVI** | Proprietary container |
| **MOV** | Proprietary container |
| **WMV** | Proprietary Microsoft format |
| **FLV** | Proprietary Flash format |
| **Any DRM-protected** | Conflicts with free licensing |

> ⚠️ **This is a common point of confusion.** Many users upload MP4 files and wonder why they're rejected. Commons cannot accept H.264/H.265 video due to patent licensing, even if the content itself is freely licensed. Always convert to WebM (VP9 or AV1) before uploading.

### Conversion Patterns (ffmpeg)

```bash
# Convert MP4 to WebM (VP9 — best quality)
ffmpeg -i input.mp4 -c:v libvpx-vp9 -c:a libopus -b:v 0 -crf 30 -b:a 96k output.webm

# Convert to WebM (VP8 — wider compatibility, slightly lower quality)
ffmpeg -i input.mp4 -c:v libvpx -c:a libvorbis -b:v 1M -crf 10 output.webm

# Convert to OGV (Theora — legacy)
ffmpeg -i input.mp4 -c:v libtheora -c:a libvorbis -q:v 7 output.ogv

# Resize to 720p while converting
ffmpeg -i input.mp4 -c:v libvpx-vp9 -c:a libopus -vf "scale=-1:720" output.webm
```

### Recommended Codecs for New Uploads

| Priority | Codec | Quality | File Size | Browser Support |
|:--------:|-------|---------|-----------|----------------|
| 1 🥇 | **VP9** (WebM) | Excellent | Good | All modern browsers |
| 2 🥈 | **AV1** (WebM) | Best | Smallest | Newer browsers only |
| 3 | **VP8** (WebM) | Good | Larger | Universal (even old browsers) |
| 4 | **Theora** (OGV) | Acceptable | Large | Legacy |

> 💡 **VP9 is the sweet spot** for most uploads: excellent quality, good compression, universal browser support. Use AV1 if file size is critical and you can accept less browser coverage.

---

## 3. Uploading Audio and Video

### The `video2commons` Tool

**[video2commons](https://commons.wikimedia.org/wiki/Commons:Video2Commons)** is the primary tool for uploading audio and video to Commons. It handles both audio and video, including automatic transcoding.

**Features:**
- Accepts MP4, AVI, MOV, and other blocked formats as **source** and transcodes them to WebM/OGG during upload
- Supports YouTube URL import (if the video is under a compatible license)
- Preserves metadata during transcoding
- Handles large files with chunked upload

```bash
# Install video2commons (Python tool)
pip install video2commons

# Upload a file (interactive — prompts for metadata)
video2commons upload input.mp4

# Batch upload from a list
video2commons upload list.txt
```

### Uploading via the Action API (Direct Upload)

You can upload already-transcoded WebM/OGG files directly via the API:

```python
import requests

SESSION = requests.Session()
SESSION.auth = ("User@botname", "bot_password")
SESSION.headers.update({"User-Agent": "MyBot/1.0 (user@example.com)"})

# Get CSRF token
token_resp = SESSION.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query", "meta": "tokens", "type": "csrf", "format": "json",
})
csrf_token = token_resp.json()["query"]["tokens"]["csrftoken"]

# Upload
with open("my_video.webm", "rb") as f:
    resp = SESSION.post("https://commons.wikimedia.org/w/api.php", data={
        "action": "upload",
        "filename": "My_Video.webm",
        "comment": "Uploading a video about topic X",
        "text": "== {{int:filedesc}} ==\n{{Information\n|description=Description of the video\n|date=2026-01-01\n|source={{own}}\n|author=[[User:Me|Me]]\n|other_versions=\n}}\n\n== {{int:license-header}} ==\n{{self|cc-by-sa-4.0}}\n\n[[Category:Educational videos]]",
        "token": csrf_token,
        "format": "json",
    }, files={"file": f})
```

> 🔗 **Authentication setup:** See **[wikimedia-auth-oauth](../wikimedia-auth-oauth/SKILL.md)** for bot passwords and CSRF token handling.

### File Size Considerations

- Audio files are typically small (a few MB to tens of MB)
- Video files can be **very large** (hundreds of MB to GBs for high-resolution content)
- For files over 100 MB, use chunked uploads or `video2commons` which handles this automatically
- Commons has per-project size limits — extremely large files may need special permission

---

## 4. Metadata via the Action API

Audio and video metadata is accessed through `prop=imageinfo` with `iiprop=metadata`. The structure differs depending on the file type.

### Audio Metadata

```python
import requests

resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "imageinfo",
    "iiprop": "size|mime|metadata|mediatype",
    "titles": "File:My_Audio.ogg",
    "format": "json",
}, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})

page = next(iter(resp.json()["query"]["pages"].values()))
info = page.get("imageinfo", [{}])[0]

print(f"MIME:        {info.get('mime')}")           # → "application/ogg" or "audio/ogg"
print(f"Mediatype:   {info.get('mediatype')}")      # → "AUDIO"
print(f"File size:   {info.get('size')} bytes")

# Parse stream metadata
for meta in info.get("metadata", []):
    if meta["name"] == "length":
        print(f"Duration:    {float(meta['value']):.1f}s")
    elif meta["name"] == "streams":
        for stream in meta["value"]:
            for item in stream.get("value", []):
                if item["name"] == "type" and item["value"] == "Vorbis":
                    # Found audio stream — look for details
                    pass
```

### Audio Metadata Fields

| Field | Source | Example |
|-------|--------|---------|
| Duration | `length` (in stream metadata) | `2.81` (seconds) |
| Sample rate | `audio_sample_rate` | `22050` (Hz) |
| Channels | `audio_channels` | `1` (mono), `2` (stereo) |
| Codec | `type` (in stream) | `Vorbis`, `Opus`, `FLAC` |
| Bitrate | `bitrate_nominal` | `40222` (bps) |
| Encoder | `vendor` or `encoder` | `Lavc59.37.100 libvorbis` |

### Video Metadata

```python
resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "imageinfo",
    "iiprop": "size|mime|metadata|mediatype",
    "titles": "File:My_Video.webm",
    "format": "json",
}, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})

page = next(iter(resp.json()["query"]["pages"].values()))
info = page.get("imageinfo", [{}])[0]

print(f"MIME:        {info.get('mime')}")           # → "video/webm"
print(f"Mediatype:   {info.get('mediatype')}")      # → "VIDEO"
print(f"Resolution:  {info.get('width')}×{info.get('height')}")
print(f"File size:   {info.get('size')} bytes")

# Parse the flat metadata object
for meta in info.get("metadata", []):
    name = meta.get("name", "")
    if name == "playtime_seconds":
        print(f"Duration:    {float(meta['value']):.1f}s")
    elif name == "playtime_string":
        print(f"Duration:    {meta['value']}")       # → "10:58"

    # Parse video stream info
    if name == "video" and isinstance(meta.get("value"), list):
        for vitem in meta["value"]:
            vname = vitem.get("name", "")
            if vname == "dataformat":
                print(f"Video codec: {vitem['value']}")   # → "V_VP9"
            elif vname == "resolution_x":
                print(f"Res X:       {vitem['value']}")
            elif vname == "resolution_y":
                print(f"Res Y:       {vitem['value']}")

    # Parse audio stream info (video has embedded audio)
    if name == "audio" and isinstance(meta.get("value"), list):
        for aitem in meta["value"]:
            aname = aitem.get("name", "")
            if aname == "dataformat":
                print(f"Audio codec:  {aitem['value']}")  # → "A_OPUS"
            elif aname == "sample_rate":
                print(f"Sample rate:  {aitem['value']}")
            elif aname == "channels":
                print(f"Channels:     {aitem['value']}")
```

### Video Metadata Fields

| Field | Source | Example |
|-------|--------|---------|
| Duration | `playtime_seconds` | `658.088` (seconds) |
| Duration (formatted) | `playtime_string` | `"10:58"` |
| Video codec | `video[].dataformat` | `"V_VP9"`, `"V_VP8"`, `"V_AV1"` |
| Resolution | `video[].resolution_x/y` | `1920`, `1080` |
| Audio codec | `audio[].dataformat` | `"A_OPUS"`, `"A_VORBIS"` |
| Sample rate | `audio[].sample_rate` | `48000` |
| Channels | `audio[].channels` | `2`, `6` |
| Bitrate | `bitrate` | `10212352` (bps) |
| File format | `fileformat` | `"webm"` |

### The `mediatype` Field

The API provides a top-level `mediatype` field to distinguish file types:

| Value | File Type |
|-------|-----------|
| `AUDIO` | Audio-only files |
| `VIDEO` | Video files (may include embedded audio) |
| `BITMAP` | Raster images |
| `DRAWING` | Vector images (SVG) |
| `OFFICE` | Documents (PDF, DjVu) |
| `TEXT` | Text documents |
| `MULTIMEDIA` | Other interactive media |
| `ARCHIVE` | Archive files |
| `EXECUTABLE` | Executable files (rare on Commons) |
| `UNKNOWN` | Unknown media type |

---

## 5. Thumbnails for Audio and Video

### Video Keyframe Thumbnails

Commons generates a **single-frame JPEG thumbnail** for video files by extracting a keyframe (typically near the start of the video).

**Thumb URL pattern:**
```
https://upload.wikimedia.org/wikipedia/commons/thumb/{hash}/{filename}/{width}px--{filename}.jpg
```

Note the `--` (double dash) in the URL — this differs from the `-{name}` pattern used for images and the `page{N}-` pattern used for documents.

```python
resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "imageinfo",
    "iiprop": "url|thumbmime",
    "iiurlwidth": 400,
    "titles": "File:Elephants Dream (2006).webm",
    "format": "json",
}, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})

info = next(iter(resp.json()["query"]["pages"].values()))["imageinfo"][0]
print(f"Thumb URL:  {info['thumburl']}")      # → .../500px--Elephants_Dream_...webm.jpg
print(f"Thumb MIME: {info['thumbmime']}")      # → image/jpeg
print(f"Retina:     {info.get('responsiveUrls', {}).get('2')}")
```

> 🔗 **General thumbnail mechanics:** See **[wikimedia-commons-thumbnails](../wikimedia-commons-thumbnails/SKILL.md)** (Section 4: Format Conversion Matrix) for the full system.

### Audio "Thumbnails"

Audio files do **not** have a meaningful visual thumbnail. The `iiurlwidth` parameter still works (returns a generic speaker icon or waveform placeholder), but the result is not useful for display purposes.

```python
# Audio files return a placeholder thumbnail (generic icon)
info = next(iter(resp.json()["query"]["pages"].values()))["imageinfo"][0]
print(f"thumburl: {info['thumburl']}")   # → generic icon, not a real preview
```

---

## 6. The Player Widget

Commons uses the **TimedMediaHandler** extension to provide audio and video playback. Players are embedded automatically when a media file is included in a page.

### Embedding in Wikipedia Articles

```wikitext
# Basic audio
[[File:My_Audio.ogg]]

# Audio with thumbnail appearance
[[File:My_Audio.ogg|thumb|Audio description]]

# Basic video
[[File:My_Video.webm]]

# Video with sizing and thumbnail appearance
[[File:My_Video.webm|thumb|400px|Video description]]

# Frameless video (no border, no caption)
[[File:My_Video.webm|frameless|400px]]

# Center-aligned
[[File:My_Video.webm|center|400px]]
```

### Player Features

| Feature | Audio | Video |
|---------|-------|-------|
| Play / Pause | ✅ | ✅ |
| Seek bar | ✅ | ✅ |
| Volume control | ✅ | ✅ |
| Time display | ✅ | ✅ |
| Fullscreen | ❌ | ✅ |
| Playback speed | ✅ | ✅ |
| Subtitles | ✅ | ✅ |
| Picture-in-picture | ❌ | ✅ |

### HTML5 `<video>` / `<audio>` Fallback

When embedding via `[[File:]]`, MediaWiki generates appropriate `<video>` or `<audio>` HTML5 elements with the Commons player as a fallback. The player also supports **multiple source formats** — if a WebM is available (via transcoding), it will be used instead of OGV when the browser supports it.

---

## 7. TimedText (Subtitles and Captions)

TimedText is Commons's subtitle system, supporting both audio (spoken word) and video files.

### The TimedText Namespace

Subtitles are stored as pages in the **TimedText namespace** (NS 102):

```
TimedText:My_Audio.oga.en.srt     → English subtitles for My_Audio.oga
TimedText:My_Video.webm.fr.srt    → French subtitles for My_Video.webm
```

### Format

TimedText uses **SubRip (.srt)** format:

```srt
1
00:00:01,000 --> 00:00:04,500
This is the first subtitle.

2
00:00:05,000 --> 00:00:09,000
This is the second subtitle.
```

### Finding Subtitles via the API

```python
resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "list": "prefixsearch",
    "pssearch": "TimedText:My_Video.webm",
    "psnamespace": 102,
    "format": "json",
}, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})

for result in resp.json()["query"]["prefixsearch"]:
    print(f"Subtitle: {result['title']}")
    # → TimedText:My_Video.webm.en.srt
    # → TimedText:My_Video.webm.fr.srt
```

### Creating Subtitles

To add subtitles to a file:

1. Create an `.srt` file with the subtitle content
2. Upload it as a new page in the TimedText namespace

```bash
# Upload via the Action API
curl -X POST "https://commons.wikimedia.org/w/api.php" \
  -d "action=edit" \
  -d "title=TimedText:My_Video.webm.en.srt" \
  -d "text=1%0A00%3A00%3A01%2C000%20--%3E%2000%3A00%3A04%2C500%0AHello%20world" \
  -d "token=YOUR_CSRF_TOKEN" \
  -d "format=json" \
  -H "User-Agent: MyBot/1.0 (user@example.com)"
```

Once uploaded, the player automatically detects and uses subtitles when available.

---

## 8. Transcoding Pipeline

When you upload audio or video to Commons, the server automatically **transcodes** it into multiple formats for compatibility.

### What Gets Transcoded

| Source Format | Transcodes To |
|--------------|---------------|
| OGG (Vorbis) | Opus (for streaming) |
| FLAC | Ogg Vorbis (for streaming), Opus |
| WebM (VP9) | VP8 version (for older browser compatibility) |
| WebM (AV1) | VP9, VP8 |
| OGV (Theora) | VP8 (for better compression) |

### Checking Transcoding Status

```python
resp = requests.get("https://commons.wikimedia.org/w/api.php", params={
    "action": "query",
    "prop": "transcodestatus",
    "titles": "File:My_Video.webm",
    "format": "json",
}, headers={"User-Agent": "MyBot/1.0 (user@example.com)"})

transcodes = next(iter(resp.json()["query"]["pages"].values())).get("transcodestatus", {})
for key, status in transcodes.items():
    print(f"{key}: {status.get('finalState', 'unknown')}")
    # → "DONE" / "IN_PROGRESS" / "ERROR"
```

### Transcoding Duration

- **Audio**: Seconds to minutes (typically fast)
- **Video (short, <5 min)**: Minutes
- **Video (long, 30+ min)**: Can take **hours** for high-resolution VP9 transcodes
- Transcoding happens asynchronously — check via `transcodestatus`

### Transcoding Errors

Common reasons for transcoding failure:

| Error | Likely Cause |
|-------|-------------|
| `FILE_NOT_FOUND` | File was deleted or renamed during processing |
| `TRANSCODE_ERROR` | Corrupted source file or unsupported codec feature |
| `TIMEOUT` | File was too large or complex to transcode within the time limit |
| `NO_TRANSCODE_NEEDED` | File is already in an optimal format |

---

## 9. Editing and Derivatives

### Commons Is Not a Video Editor

Commons is a **repository**, not an editing tool. All editing must happen locally before uploading.

### Clipping and Trimming

```bash
# Extract a 30-second clip starting at 1:00
ffmpeg -i input.webm -ss 00:01:00 -t 30 -c copy output.webm

# Trim start and end (keep from 0:30 to 2:00)
ffmpeg -i input.webm -ss 00:00:30 -to 00:02:00 -c copy output.webm
```

### Recommended Editing Software

| Task | Tool |
|------|------|
| Video editing | [Kdenlive](https://kdenlive.org/) (open-source), [Blender](https://www.blender.org/) (VSE), [DaVinci Resolve](https://www.blackmagicdesign.com/products/davinciresolve) |
| Audio editing | [Audacity](https://www.audacityteam.org/) (open-source) |
| Conversion | [ffmpeg](https://ffmpeg.org/) |
| Subtitling | [Aegisub](https://aegisub.org/) (open-source) |

### Marking Derivatives

When you create a derivative work from an existing Commons file, use the `{{Derived from}}` or `{{Extracted from}}` template:

```wikitext
{{Derived from|Original_File.webm|by=[[User:Me]]}}
```

This ensures proper attribution and licensing chain.

### License Compatibility

When creating derivatives:

| Source License | Derivative Must Be |
|---------------|-------------------|
| CC BY-SA 4.0 | CC BY-SA 4.0 (or compatible) |
| CC BY 4.0 | CC BY 4.0 or CC BY-SA 4.0 |
| CC0 | Any license (CC0, CC BY, CC BY-SA) |
| Public Domain | Any license |

> ⚠️ **Music licensing is complex.** A video may contain multiple copyrighted elements (soundtrack, spoken word, visual footage) under different licenses. Ensure all components are compatible with the license you choose for the derivative.

---

## 10. Legal and Attribution

### Patent Concerns

The format restrictions (no H.264, no H.265, no AAC, no MP2) stem from **software patent licensing**:

- **H.264/AVC**: Patented by MPEG LA. Requires licensing fees for encoder/decoder implementations in some contexts
- **H.265/HEVC**: Even more complex patent landscape
- **AAC**: Patented
- **MP3**: Most patents have now expired, but MP3 is still discouraged as a matter of policy consistency

The allowed formats (VP8, VP9, AV1, Vorbis, Opus, FLAC, Theora) are:
- Covered by royalty-free patent grants (WebM, AV1)
- Published as open standards (IETF RFCs for Opus, Vorbis)
- Implementable without patent licensing fees

### Attribution for Multimedia

Attribution works the same as for images, but can be more complex for multimedia with multiple contributors:

- **Video**: May have separate attribution for footage, soundtrack, narration
- **Audio**: May have separate attribution for performance, composition, recording

The `{{Information}}` template supports multiple authors and sources via the `author` and `source` fields.

---

## Related Skills

| Skill | Relevance |
|-------|-----------|
| **[wikimedia-api-access](../wikimedia-api-access/SKILL.md)** | User-Agent, rate limiting, error handling |
| **[wikimedia-commons](../wikimedia-commons/SKILL.md)** | File search, categories, upload basics |
| **[wikimedia-commons-thumbnails](../wikimedia-commons-thumbnails/SKILL.md)** | Video keyframe thumbnails, thumb URL scheme, `thumbmime` |
| **[wikimedia-commons-sdc](../wikimedia-commons-sdc/SKILL.md)** | Structured data for multimedia files (depicts, creator, license) |
| **[wikimedia-auth-oauth](../wikimedia-auth-oauth/SKILL.md)** | Authentication for uploading audio/video |
