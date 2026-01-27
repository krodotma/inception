"""
YouTube acquisition module.

Handles downloading videos, audio, subtitles, and metadata from YouTube
using yt-dlp.
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from inception.config import get_config


@dataclass
class VideoMetadata:
    """Metadata extracted from a YouTube video."""
    
    video_id: str
    title: str
    description: str | None = None
    channel: str | None = None
    channel_id: str | None = None
    upload_date: datetime | None = None
    duration_seconds: int | None = None
    view_count: int | None = None
    like_count: int | None = None
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    thumbnail_url: str | None = None
    chapters: list[dict[str, Any]] = field(default_factory=list)
    subtitles_available: list[str] = field(default_factory=list)
    automatic_captions: list[str] = field(default_factory=list)
    
    @classmethod
    def from_yt_dlp_info(cls, info: dict[str, Any]) -> VideoMetadata:
        """Create from yt-dlp info dict."""
        upload_date = None
        if info.get("upload_date"):
            try:
                upload_date = datetime.strptime(info["upload_date"], "%Y%m%d")
            except ValueError:
                pass
        
        return cls(
            video_id=info.get("id", ""),
            title=info.get("title", ""),
            description=info.get("description"),
            channel=info.get("channel") or info.get("uploader"),
            channel_id=info.get("channel_id") or info.get("uploader_id"),
            upload_date=upload_date,
            duration_seconds=info.get("duration"),
            view_count=info.get("view_count"),
            like_count=info.get("like_count"),
            tags=info.get("tags") or [],
            categories=info.get("categories") or [],
            thumbnail_url=info.get("thumbnail"),
            chapters=info.get("chapters") or [],
            subtitles_available=list((info.get("subtitles") or {}).keys()),
            automatic_captions=list((info.get("automatic_captions") or {}).keys()),
        )


@dataclass
class DownloadResult:
    """Result of a video download operation."""
    
    video_id: str
    metadata: VideoMetadata
    audio_path: Path | None = None
    video_path: Path | None = None
    subtitle_paths: dict[str, Path] = field(default_factory=dict)
    thumbnail_path: Path | None = None
    info_json_path: Path | None = None
    
    @property
    def has_subtitles(self) -> bool:
        return bool(self.subtitle_paths)
    
    @property
    def subtitle_languages(self) -> list[str]:
        return list(self.subtitle_paths.keys())


def parse_youtube_url(url: str) -> dict[str, Any]:
    """
    Parse a YouTube URL and extract video/channel/playlist info.
    
    Returns:
        Dict with keys:
        - type: 'video', 'channel', 'playlist', or 'unknown'
        - video_id: for video URLs
        - channel_id: for channel URLs
        - playlist_id: for playlist URLs
        - url: normalized URL
    """
    parsed = urlparse(url)
    
    # Handle various YouTube URL formats
    if parsed.hostname in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        # Video: /watch?v=VIDEO_ID
        if parsed.path == "/watch":
            params = parse_qs(parsed.query)
            video_id = params.get("v", [None])[0]
            if video_id:
                return {
                    "type": "video",
                    "video_id": video_id,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                }
        
        # Playlist: /playlist?list=PLAYLIST_ID
        if parsed.path == "/playlist":
            params = parse_qs(parsed.query)
            playlist_id = params.get("list", [None])[0]
            if playlist_id:
                return {
                    "type": "playlist",
                    "playlist_id": playlist_id,
                    "url": f"https://www.youtube.com/playlist?list={playlist_id}",
                }
        
        # Channel: /@handle or /channel/CHANNEL_ID or /c/NAME or /user/NAME
        if parsed.path.startswith("/@"):
            handle = parsed.path[2:]
            return {
                "type": "channel",
                "channel_handle": handle,
                "url": f"https://www.youtube.com/@{handle}",
            }
        
        if parsed.path.startswith("/channel/"):
            channel_id = parsed.path.split("/")[2]
            return {
                "type": "channel",
                "channel_id": channel_id,
                "url": f"https://www.youtube.com/channel/{channel_id}",
            }
        
        for prefix in ("/c/", "/user/"):
            if parsed.path.startswith(prefix):
                name = parsed.path.split("/")[2]
                return {
                    "type": "channel",
                    "channel_name": name,
                    "url": url,
                }
    
    # Short URLs: youtu.be/VIDEO_ID
    if parsed.hostname == "youtu.be":
        video_id = parsed.path.lstrip("/")
        if video_id:
            return {
                "type": "video",
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
    
    return {"type": "unknown", "url": url}


def fetch_video_metadata(url: str) -> VideoMetadata:
    """
    Fetch metadata for a YouTube video without downloading.
    
    Args:
        url: YouTube video URL
    
    Returns:
        VideoMetadata object
    
    Raises:
        RuntimeError: If yt-dlp fails
    """
    config = get_config()
    
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--no-download",
        "--no-playlist",
        url,
    ]
    
    if config.pipeline.offline_mode:
        raise RuntimeError("Cannot fetch metadata in offline mode")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        return VideoMetadata.from_yt_dlp_info(info)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"yt-dlp failed: {e.stderr}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse yt-dlp output: {e}") from e


def download_video(
    url: str,
    output_dir: Path | None = None,
    download_video: bool = False,
    download_audio: bool = True,
    download_subtitles: bool = True,
    download_thumbnail: bool = True,
    preferred_languages: list[str] | None = None,
) -> DownloadResult:
    """
    Download a YouTube video with optional components.
    
    Args:
        url: YouTube video URL
        output_dir: Directory to save files (default: config artifacts dir)
        download_video: Whether to download video stream
        download_audio: Whether to download audio stream
        download_subtitles: Whether to download subtitles
        download_thumbnail: Whether to download thumbnail
        preferred_languages: Preferred subtitle languages (default: ["en"])
    
    Returns:
        DownloadResult with paths to downloaded files
    """
    config = get_config()
    
    if config.pipeline.offline_mode:
        raise RuntimeError("Cannot download in offline mode")
    
    if output_dir is None:
        output_dir = config.artifacts_dir / "youtube"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if preferred_languages is None:
        preferred_languages = ["en"]
    
    # First, get metadata
    metadata = fetch_video_metadata(url)
    
    # Create video-specific output directory
    video_dir = output_dir / metadata.video_id
    video_dir.mkdir(parents=True, exist_ok=True)
    
    result = DownloadResult(
        video_id=metadata.video_id,
        metadata=metadata,
    )
    
    # Download info JSON
    info_path = video_dir / "info.json"
    _run_yt_dlp(url, video_dir, ["--write-info-json", "--skip-download"])
    json_files = list(video_dir.glob("*.info.json"))
    if json_files:
        result.info_json_path = json_files[0]
    
    # Download audio
    if download_audio:
        audio_opts = [
            "-f", "bestaudio[ext=m4a]/bestaudio",
            "-o", str(video_dir / "audio.%(ext)s"),
        ]
        _run_yt_dlp(url, video_dir, audio_opts)
        audio_files = list(video_dir.glob("audio.*"))
        if audio_files:
            result.audio_path = audio_files[0]
    
    # Download video
    if download_video:
        video_opts = [
            "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
            "-o", str(video_dir / "video.%(ext)s"),
        ]
        _run_yt_dlp(url, video_dir, video_opts)
        video_files = [f for f in video_dir.glob("video.*") if not f.suffix == ".json"]
        if video_files:
            result.video_path = video_files[0]
    
    # Download subtitles
    if download_subtitles:
        sub_opts = [
            "--write-subs",
            "--write-auto-subs",
            "--sub-format", "vtt/srt/best",
            "--sub-langs", ",".join(preferred_languages) + ",en",
            "--skip-download",
            "-o", str(video_dir / "subs.%(ext)s"),
        ]
        _run_yt_dlp(url, video_dir, sub_opts)
        
        # Find downloaded subtitle files
        for sub_file in video_dir.glob("*.vtt"):
            # Extract language from filename
            lang = _extract_lang_from_subtitle_file(sub_file)
            if lang:
                result.subtitle_paths[lang] = sub_file
        
        for sub_file in video_dir.glob("*.srt"):
            lang = _extract_lang_from_subtitle_file(sub_file)
            if lang and lang not in result.subtitle_paths:
                result.subtitle_paths[lang] = sub_file
    
    # Download thumbnail
    if download_thumbnail:
        thumb_opts = [
            "--write-thumbnail",
            "--convert-thumbnails", "jpg",
            "--skip-download",
            "-o", str(video_dir / "thumbnail.%(ext)s"),
        ]
        _run_yt_dlp(url, video_dir, thumb_opts)
        thumb_files = list(video_dir.glob("thumbnail.*"))
        if thumb_files:
            result.thumbnail_path = thumb_files[0]
    
    return result


def _run_yt_dlp(url: str, output_dir: Path, extra_opts: list[str]) -> subprocess.CompletedProcess:
    """Run yt-dlp with the given options."""
    cmd = ["yt-dlp", "--no-playlist"] + extra_opts + [url]
    
    try:
        return subprocess.run(
            cmd,
            cwd=output_dir,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        # Log but don't fail for non-critical downloads
        pass
    
    return subprocess.CompletedProcess(cmd, 0)


def _extract_lang_from_subtitle_file(path: Path) -> str | None:
    """Extract language code from subtitle filename."""
    # Pattern: name.LANG.vtt or name.LANG.srt
    stem = path.stem
    parts = stem.rsplit(".", 1)
    if len(parts) == 2:
        lang = parts[1]
        # Validate it looks like a language code
        if re.match(r"^[a-z]{2}(-[A-Z]{2})?$", lang):
            return lang
    return None


def list_channel_videos(
    channel_url: str,
    since: datetime | None = None,
    until: datetime | None = None,
    max_videos: int | None = None,
) -> list[dict[str, Any]]:
    """
    List videos from a YouTube channel.
    
    Args:
        channel_url: YouTube channel URL
        since: Only include videos uploaded after this date
        until: Only include videos uploaded before this date
        max_videos: Maximum number of videos to return
    
    Returns:
        List of video info dicts with id, title, upload_date, duration
    """
    config = get_config()
    
    if config.pipeline.offline_mode:
        raise RuntimeError("Cannot list channel in offline mode")
    
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        channel_url,
    ]
    
    if max_videos:
        cmd.extend(["--playlist-end", str(max_videos)])
    
    if since:
        cmd.extend(["--dateafter", since.strftime("%Y%m%d")])
    
    if until:
        cmd.extend(["--datebefore", until.strftime("%Y%m%d")])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        videos = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    info = json.loads(line)
                    videos.append({
                        "id": info.get("id"),
                        "title": info.get("title"),
                        "url": f"https://www.youtube.com/watch?v={info.get('id')}",
                        "duration": info.get("duration"),
                    })
                except json.JSONDecodeError:
                    continue
        
        return videos
    
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"yt-dlp failed: {e.stderr}") from e


def list_playlist_videos(
    playlist_url: str,
    max_videos: int | None = None,
) -> list[dict[str, Any]]:
    """
    List videos from a YouTube playlist.
    
    Args:
        playlist_url: YouTube playlist URL
        max_videos: Maximum number of videos to return
    
    Returns:
        List of video info dicts
    """
    config = get_config()
    
    if config.pipeline.offline_mode:
        raise RuntimeError("Cannot list playlist in offline mode")
    
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        playlist_url,
    ]
    
    if max_videos:
        cmd.extend(["--playlist-end", str(max_videos)])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        videos = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    info = json.loads(line)
                    videos.append({
                        "id": info.get("id"),
                        "title": info.get("title"),
                        "url": f"https://www.youtube.com/watch?v={info.get('id')}",
                        "duration": info.get("duration"),
                    })
                except json.JSONDecodeError:
                    continue
        
        return videos
    
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"yt-dlp failed: {e.stderr}") from e
