import json
import os
from typing import Dict, Any, Optional, List


class ConfigManager:
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.config = {}
        self.load_config()

    def load_config(self):
        """Загрузить конфигурацию из файла"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки конфигурации: {e}")
                self._create_default_config()
        else:
            self._create_default_config()

    def _create_default_config(self):
        """Создать конфигурацию по умолчанию"""
        self.config = {
            "default_download_path": "./downloads",
            "max_concurrent_downloads": 3,
            "theme": "dark",
            "filename_template": "%(title)s.%(ext)s",
            "max_retries": 3,
            "socket_timeout": 30,
            "profiles": {
                "default": {
                    "name": "По умолчанию",
                    "format": "best",
                    "quality": "best",
                    "use_cookies": False,
                    "write_subs": False,
                    "sub_lang": "ru",
                    "embed_thumbnail": False,
                    "write_metadata": True
                }
            }
        }
        self.save_config()

    def save_config(self):
        """Сохранить конфигурацию в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения конфигурации: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Получить значение настройки"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Установить значение настройки"""
        self.config[key] = value
        self.save_config()

    def create_profile(self, name: str, settings: Dict[str, Any]) -> bool:
        """Создать новый профиль настроек"""
        if 'profiles' not in self.config:
            self.config['profiles'] = {}

        profile_id = name.lower().replace(' ', '_')

        if profile_id in self.config['profiles']:
            return False

        self.config['profiles'][profile_id] = {
            'name': name,
            **settings
        }
        self.save_config()
        return True

    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Получить профиль по ID"""
        return self.config.get('profiles', {}).get(profile_id)

    def get_all_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Получить все профили"""
        return self.config.get('profiles', {})

    def update_profile(self, profile_id: str, settings: Dict[str, Any]) -> bool:
        """Обновить профиль"""
        if 'profiles' not in self.config or profile_id not in self.config['profiles']:
            return False

        self.config['profiles'][profile_id].update(settings)
        self.save_config()
        return True

    def delete_profile(self, profile_id: str) -> bool:
        """Удалить профиль"""
        if profile_id == 'default':
            return False

        if 'profiles' in self.config and profile_id in self.config['profiles']:
            del self.config['profiles'][profile_id]
            self.save_config()
            return True
        return False

    def duplicate_profile(self, profile_id: str, new_name: str) -> bool:
        """Дублировать профиль"""
        profile = self.get_profile(profile_id)
        if not profile:
            return False

        new_profile = profile.copy()
        new_profile['name'] = new_name

        new_profile_id = new_name.lower().replace(' ', '_')
        return self.create_profile(new_name, new_profile)

    def get_profile_list(self) -> List[Dict[str, str]]:
        """Получить список профилей для отображения в GUI"""
        profiles = []
        for profile_id, profile_data in self.config.get('profiles', {}).items():
            profiles.append({
                'id': profile_id,
                'name': profile_data.get('name', profile_id)
            })
        return profiles
