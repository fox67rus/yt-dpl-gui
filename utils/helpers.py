import os
import shutil
import platform
from typing import Optional


def find_ffmpeg(configured_path: str = '') -> Optional[str]:
    """
    Ищет ffmpeg в порядке приоритета:
    1. Путь из настроек
    2. Корень проекта (рядом с main.py)
    3. Системный PATH
    Возвращает директорию с ffmpeg (для ffmpeg_location) или None.
    """
    exe = 'ffmpeg.exe' if platform.system() == 'Windows' else 'ffmpeg'

    if configured_path:
        candidate = configured_path.strip()
        if os.path.isfile(candidate):
            return os.path.dirname(candidate)
        if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, exe)):
            return candidate

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    root_ffmpeg = os.path.join(project_root, exe)
    if os.path.isfile(root_ffmpeg):
        return project_root

    if shutil.which('ffmpeg'):
        return None  # None = yt-dlp ищет в PATH сам

    return ''  # пустая строка = ffmpeg не найден


def format_filesize(bytes_size: int) -> str:
    """Форматировать размер файла в читаемый вид"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"


def format_duration(seconds: int) -> str:
    """Форматировать длительность в читаемый вид"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def sanitize_filename(filename: str) -> str:
    """Очистить имя файла от недопустимых символов"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename
