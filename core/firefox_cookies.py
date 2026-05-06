import os
import platform
import glob
import shutil
import sqlite3
import tempfile
import configparser
from datetime import datetime
from typing import Optional, Tuple


def _get_firefox_base_dir() -> Optional[str]:
    """Вернуть корневую директорию Firefox (где лежит profiles.ini)."""
    system = platform.system()
    if system == 'Windows':
        return os.path.join(os.getenv('APPDATA', ''), 'Mozilla', 'Firefox')
    elif system == 'Darwin':
        return os.path.expanduser('~/Library/Application Support/Firefox')
    elif system == 'Linux':
        return os.path.expanduser('~/.mozilla/firefox')
    return None


def get_firefox_profile_path() -> Optional[str]:
    """Найти путь к активному профилю Firefox."""
    base_dir = _get_firefox_base_dir()
    if not base_dir or not os.path.exists(base_dir):
        return None

    # 1. Читаем profiles.ini: секция Install* содержит активный профиль
    profiles_ini = os.path.join(base_dir, 'profiles.ini')
    if os.path.exists(profiles_ini):
        cfg = configparser.ConfigParser()
        cfg.read(profiles_ini, encoding='utf-8')

        # Секция вида InstallXXXXXXX имеет ключ 'default' с относительным путём профиля
        for section in cfg.sections():
            if section.lower().startswith('install') and 'default' in cfg[section]:
                rel_path = cfg[section]['default']
                full_path = os.path.join(base_dir, rel_path.replace('/', os.sep))
                if os.path.isdir(full_path):
                    return full_path

        # Запасной вариант: Profile* с isrelative=1, ищем тот у которого есть cookies.sqlite
        candidates = []
        for section in cfg.sections():
            if section.lower().startswith('profile') and 'path' in cfg[section]:
                rel = cfg[section]['path']
                is_relative = cfg[section].get('isrelative', '0') == '1'
                full_path = os.path.join(base_dir, rel.replace('/', os.sep)) if is_relative else rel
                if os.path.isdir(full_path):
                    candidates.append(full_path)

        # Предпочитаем профиль с cookies.sqlite, затем default-release, затем любой
        for path in candidates:
            if os.path.exists(os.path.join(path, 'cookies.sqlite')):
                return path
        for path in candidates:
            if 'default-release' in os.path.basename(path):
                return path
        if candidates:
            return candidates[0]

    # 2. Фолбэк: glob по директории Profiles
    profiles_dir = os.path.join(base_dir, 'Profiles')
    search_dir = profiles_dir if os.path.isdir(profiles_dir) else base_dir
    profiles = glob.glob(os.path.join(search_dir, '*.default*'))
    if not profiles:
        profiles = glob.glob(os.path.join(search_dir, '*'))

    # Предпочитаем профиль с cookies.sqlite
    for path in profiles:
        if os.path.isdir(path) and os.path.exists(os.path.join(path, 'cookies.sqlite')):
            return path
    dirs = [p for p in profiles if os.path.isdir(p)]
    return dirs[0] if dirs else None


def get_firefox_cookies_path() -> Optional[str]:
    """Найти путь к cookies.sqlite Firefox"""
    profile_path = get_firefox_profile_path()

    if not profile_path:
        return None

    cookies_path = os.path.join(profile_path, 'cookies.sqlite')

    if os.path.exists(cookies_path):
        return cookies_path

    return None


def check_firefox_cookies_available() -> bool:
    """Проверить доступность cookies Firefox"""
    return get_firefox_cookies_path() is not None


def export_cookies_to_file(output_path: str) -> Tuple[bool, str]:
    """
    Экспортирует YouTube-куки из Firefox в файл формата Netscape.
    Возвращает (успех, сообщение).
    """
    cookies_sqlite = get_firefox_cookies_path()
    if not cookies_sqlite:
        return False, "Файл cookies.sqlite Firefox не найден"

    tmp_db = None
    try:
        # Копируем БД во временный файл, чтобы не блокировать Firefox
        tmp_fd, tmp_db = tempfile.mkstemp(suffix='.sqlite')
        os.close(tmp_fd)
        shutil.copy2(cookies_sqlite, tmp_db)

        conn = sqlite3.connect(tmp_db)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT host, path, isSecure, expiry, name, value
            FROM moz_cookies
            WHERE host LIKE '%youtube.com'
               OR host LIKE '%google.com'
               OR host LIKE '%ytimg.com'
               OR host LIKE '%googlevideo.com'
               OR host LIKE '%yandex.ru'
               OR host LIKE '%yandex.com'
               OR host LIKE '%music.yandex.ru'
            ORDER BY host, name
        """)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return False, "YouTube-куки в Firefox не найдены"

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write(f"# Exported from Firefox by yt-dlp-gui on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            for host, path, is_secure, expiry, name, value in rows:
                include_subdomains = "TRUE" if host.startswith('.') else "FALSE"
                secure = "TRUE" if is_secure else "FALSE"
                expiry = expiry or 0
                f.write(f"{host}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n")

        return True, f"Экспортировано {len(rows)} куки → {output_path}"

    except Exception as e:
        return False, f"Ошибка экспорта: {e}"
    finally:
        if tmp_db and os.path.exists(tmp_db):
            try:
                os.remove(tmp_db)
            except OSError:
                pass


def get_firefox_status() -> dict:
    """Получить статус Firefox cookies для отображения в GUI"""
    profile_path = get_firefox_profile_path()
    cookies_path = get_firefox_cookies_path()

    return {
        'available': cookies_path is not None,
        'profile_path': profile_path or 'Не найден',
        'cookies_path': cookies_path or 'Не найден',
    }
