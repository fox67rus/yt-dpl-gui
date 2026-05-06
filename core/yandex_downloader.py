import os
import re
import threading
from typing import Optional, Callable, List, Dict, Any

from yandex_music import Client, Track


class YandexDownloader:
    def __init__(self, token: str, progress_callback: Optional[Callable] = None):
        self.token = token
        self.progress_callback = progress_callback
        self._client: Optional[Client] = None

    @staticmethod
    def _extract_token(raw: str) -> str:
        """Extract bare access_token from stored value (handles dict-as-string)."""
        raw = raw.strip()
        if raw.startswith('{'):
            import ast, re
            try:
                d = ast.literal_eval(raw)
                return d.get('access_token', raw)
            except Exception:
                m = re.search(r"'access_token'\s*:\s*'([^']+)'", raw)
                if m:
                    return m.group(1)
        return raw

    def _get_client(self) -> Client:
        token = self._extract_token(self.token)
        if self._client is None or self._client.token != token:
            self._client = Client(token).init()
        return self._client

    def update_token(self, token: str):
        clean = self._extract_token(token)
        if clean != self._extract_token(self.token):
            self.token = token
            self._client = None

    # ------------------------------------------------------------------
    # URL parsing
    # ------------------------------------------------------------------

    @staticmethod
    def parse_url(url: str) -> Dict[str, Any]:
        url = url.strip()
        # Track: /album/{album_id}/track/{track_id}
        m = re.search(r'/album/(\d+)/track/(\d+)', url)
        if m:
            return {'type': 'track', 'album_id': m.group(1), 'track_id': m.group(2)}

        # Album: /album/{album_id}
        m = re.search(r'/album/(\d+)', url)
        if m:
            return {'type': 'album', 'album_id': m.group(1)}

        # Playlist: /users/{user}/playlists/{kind}
        m = re.search(r'/users/([^/?]+)/playlists/(\d+)', url)
        if m:
            return {'type': 'playlist', 'user': m.group(1), 'kind': int(m.group(2))}

        # Artist: /artist/{artist_id}
        m = re.search(r'/artist/(\d+)', url)
        if m:
            return {'type': 'artist', 'artist_id': m.group(1)}

        return {'type': 'unknown'}

    # ------------------------------------------------------------------
    # Fetching tracks
    # ------------------------------------------------------------------

    def get_tracks_from_url(self, url: str) -> List[Track]:
        client = self._get_client()
        parsed = self.parse_url(url)

        if parsed['type'] == 'track':
            track_id = f"{parsed['track_id']}:{parsed['album_id']}"
            result = client.tracks([track_id])
            return [t for t in result if t and not getattr(t, 'error', None)]

        elif parsed['type'] == 'album':
            album = client.albums_with_tracks(parsed['album_id'])
            tracks = []
            for vol in (album.volumes or []):
                tracks.extend(vol)
            return [t for t in tracks if t and not getattr(t, 'error', None)]

        elif parsed['type'] == 'playlist':
            playlist = client.users_playlists(parsed['kind'], parsed['user'])
            return [t.track for t in (playlist.tracks or [])
                    if t.track and not getattr(t.track, 'error', None)]

        elif parsed['type'] == 'artist':
            result = client.artists_tracks(parsed['artist_id'], page_size=100)
            return [t for t in (result.tracks or []) if not getattr(t, 'error', None)]

        raise ValueError('Нераспознанная ссылка. Поддерживаются: трек, альбом, плейлист, артист.')

    # ------------------------------------------------------------------
    # Info (preview, no download)
    # ------------------------------------------------------------------

    def get_info(self, url: str) -> Dict[str, Any]:
        parsed = self.parse_url(url)
        if parsed['type'] == 'unknown':
            raise ValueError('Нераспознанная ссылка Яндекс Музыки')

        tracks = self.get_tracks_from_url(url)
        if not tracks:
            raise ValueError('Треки не найдены')

        total_ms = sum(t.duration_ms or 0 for t in tracks)

        if len(tracks) == 1:
            t = tracks[0]
            return {
                'title': t.title or 'Unknown',
                'artist': ', '.join(t.artists_name()),
                'count': 1,
                'type': parsed['type'],
                'duration_ms': total_ms,
                'cover_uri': getattr(t, 'cover_uri', '') or '',
            }

        type_labels = {
            'album': 'Альбом',
            'playlist': 'Плейлист',
            'artist': 'Артист',
        }
        first = tracks[0]
        return {
            'title': first.title or '',
            'artist': ', '.join(first.artists_name()),
            'count': len(tracks),
            'type': parsed['type'],
            'type_label': type_labels.get(parsed['type'], ''),
            'duration_ms': total_ms,
            'cover_uri': getattr(first, 'cover_uri', '') or '',
        }

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_filename(artist: str, title: str) -> str:
        name = f"{artist} - {title}" if artist else title
        return re.sub(r'[<>:"/\\|?*\n\r]', '_', name).strip()

    def download_track(self, track: Track, output_dir: str,
                       codec: str = 'mp3', bitrate: int = 192) -> str:
        artist = ', '.join(track.artists_name())
        title = track.title or 'Unknown'
        safe = self._safe_filename(artist, title)
        os.makedirs(output_dir, exist_ok=True)

        # Find best available download option for requested codec
        download_infos = track.get_download_info()
        if not download_infos:
            raise Exception(f"Нет доступных форматов для трека: {title}")

        # Exclude previews (30-second clips)
        full_infos = [d for d in download_infos if not getattr(d, 'preview', False)]
        if not full_infos:
            # All options are previews — subscription might not cover this track
            raise Exception(
                f"Доступны только превью (30 сек) для «{title}». "
                "Проверьте, что токен получен для аккаунта с активным Яндекс Плюс."
            )

        # Filter by codec, sort by bitrate descending
        codec_options = sorted(
            [d for d in full_infos if d.codec == codec],
            key=lambda d: d.bitrate_in_kbps,
            reverse=True
        )

        if not codec_options:
            # Fallback: any codec, best bitrate
            codec_options = sorted(full_infos, key=lambda d: d.bitrate_in_kbps, reverse=True)
            codec = codec_options[0].codec

        # Pick closest bitrate to requested
        chosen = min(codec_options, key=lambda d: abs(d.bitrate_in_kbps - bitrate))

        filename = os.path.join(output_dir, f"{safe}.{codec}")
        track.download(filename, codec=chosen.codec, bitrate_in_kbps=chosen.bitrate_in_kbps)
        return filename

    def download(self, url: str, options: Dict[str, Any]) -> None:
        tracks = self.get_tracks_from_url(url)
        output_dir = options.get('output_path', './downloads')
        codec = options.get('codec', 'mp3')
        bitrate = options.get('bitrate', 192)
        total = len(tracks)

        for i, track in enumerate(tracks):
            if self.progress_callback:
                self.progress_callback({
                    'status': 'downloading',
                    'current': i + 1,
                    'total': total,
                    'title': track.title or '',
                })
            self.download_track(track, output_dir, codec, bitrate)

        if self.progress_callback:
            self.progress_callback({'status': 'finished', 'total': total})

    def download_async(self, url: str, options: Dict[str, Any],
                       completion_callback: Optional[Callable] = None) -> threading.Thread:
        def thread_func():
            try:
                self.download(url, options)
                if completion_callback:
                    completion_callback(True, None)
            except Exception as e:
                if completion_callback:
                    completion_callback(False, str(e))

        t = threading.Thread(target=thread_func, daemon=True)
        t.start()
        return t
