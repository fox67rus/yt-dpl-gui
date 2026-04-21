import os
import platform
import glob
from typing import Optional


def get_firefox_profile_path() -> Optional[str]:
    """Найти путь к профилю Firefox"""
    system = platform.system()

    if system == 'Windows':
        base_path = os.path.join(os.getenv('APPDATA'), 'Mozilla', 'Firefox', 'Profiles')
    elif system == 'Darwin':
        base_path = os.path.expanduser('~/Library/Application Support/Firefox/Profiles')
    elif system == 'Linux':
        base_path = os.path.expanduser('~/.mozilla/firefox')
    else:
        return None

    if not os.path.exists(base_path):
        return None

    profiles = glob.glob(os.path.join(base_path, '*.default*'))
    if not profiles:
        profiles = glob.glob(os.path.join(base_path, '*'))

    if profiles:
        return profiles[0]

    return None


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


def get_firefox_status() -> dict:
    """Получить статус Firefox cookies для отображения в GUI"""
    profile_path = get_firefox_profile_path()
    cookies_path = get_firefox_cookies_path()

    return {
        'available': cookies_path is not None,
        'profile_path': profile_path or 'Не найден',
        'cookies_path': cookies_path or 'Не найден',
    }
