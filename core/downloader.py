import os
import yt_dlp
import threading
from typing import Callable, Dict, Any, Optional


class YTDLPDownloader:
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.is_downloading = False

    def get_video_info(self, url: str, use_cookies: bool = False,
                       cookies_file: Optional[str] = None) -> Dict[str, Any]:
        """Получить информацию о видео без загрузки"""
        using_cookies = use_cookies or (cookies_file and os.path.isfile(cookies_file))
        player_clients = ['web'] if using_cookies else ['android', 'web']

        ydl_opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': {'player_client': player_clients}},
        }

        if use_cookies:
            ydl_opts['cookiesfrombrowser'] = ('firefox',)

        if cookies_file and os.path.isfile(cookies_file):
            ydl_opts['cookiefile'] = cookies_file

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                    'filesize': info.get('filesize') or info.get('filesize_approx', 0),
                    'formats': info.get('formats', []),
                    'uploader': info.get('uploader', 'Unknown'),
                    'description': info.get('description', ''),
                }
        except Exception as e:
            raise Exception(f"Ошибка получения информации: {str(e)}")

    def download(self, url: str, options: Dict[str, Any]) -> None:
        """Загрузка видео с настройками"""
        def progress_hook(d):
            if self.progress_callback:
                self.progress_callback(d)

        output_path = options.get('output_path', '%(title)s.%(ext)s')

        cookies_file = options.get('cookies_file')
        using_cookies = options.get('use_cookies') or (cookies_file and os.path.isfile(cookies_file))
        player_clients = ['web'] if using_cookies else ['android', 'web']

        ydl_opts = {
            'progress_hooks': [progress_hook],
            'outtmpl': output_path,
            'format': options.get('format', 'bestvideo+bestaudio/best'),
            'extractor_args': {'youtube': {'player_client': player_clients}},
        }

        ffmpeg_location = options.get('ffmpeg_location')
        if ffmpeg_location:
            ydl_opts['ffmpeg_location'] = ffmpeg_location

        if options.get('use_cookies'):
            ydl_opts['cookiesfrombrowser'] = ('firefox',)

        if cookies_file and os.path.isfile(cookies_file):
            ydl_opts['cookiefile'] = cookies_file

        if options.get('write_subs'):
            ydl_opts['writesubtitles'] = True
            ydl_opts['subtitleslangs'] = [options.get('sub_lang', 'ru')]

        postprocessors = []

        if options.get('extract_audio'):
            ydl_opts['format'] = 'bestaudio/best'
            postprocessors.append({
                'key': 'FFmpegExtractAudio',
                'preferredcodec': options.get('audio_format', 'mp3'),
                'preferredquality': options.get('audio_quality', '192'),
            })

        if options.get('write_metadata'):
            postprocessors.append({'key': 'FFmpegMetadata', 'add_metadata': True})

        if options.get('embed_thumbnail'):
            ydl_opts['writethumbnail'] = True
            postprocessors.append({'key': 'EmbedThumbnail'})

        if postprocessors:
            ydl_opts['postprocessors'] = postprocessors

        playlist_start = options.get('playlist_start')
        playlist_end = options.get('playlist_end')
        if playlist_start:
            ydl_opts['playlist_start'] = playlist_start
        if playlist_end:
            ydl_opts['playlist_end'] = playlist_end

        try:
            self.is_downloading = True
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.is_downloading = False
        except Exception as e:
            self.is_downloading = False
            raise Exception(f"Ошибка загрузки: {str(e)}")

    def download_async(self, url: str, options: Dict[str, Any],
                      completion_callback: Optional[Callable] = None) -> threading.Thread:
        """Асинхронная загрузка в отдельном потоке"""
        def download_thread():
            try:
                self.download(url, options)
                if completion_callback:
                    completion_callback(True, None)
            except Exception as e:
                if completion_callback:
                    completion_callback(False, str(e))

        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
        return thread
