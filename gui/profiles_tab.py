import customtkinter as ctk
from tkinter import simpledialog
from core.config_manager import ConfigManager


class ProfilesTab:
    def __init__(self, parent, config_manager: ConfigManager, on_profiles_changed):
        self.parent = parent
        self.config_manager = config_manager
        self.on_profiles_changed = on_profiles_changed
        self.selected_profile_id = None

        self.setup_ui()
        self.refresh_profiles()

    def setup_ui(self):
        left_frame = ctk.CTkFrame(self.parent)
        left_frame.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)

        ctk.CTkLabel(left_frame, text="Профили", font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 10))

        self.profiles_list = ctk.CTkScrollableFrame(left_frame)
        self.profiles_list.pack(fill="both", expand=True, pady=(0, 10))

        buttons_frame = ctk.CTkFrame(left_frame)
        buttons_frame.pack(fill="x")

        ctk.CTkButton(buttons_frame, text="Создать", command=self.create_profile, width=100).pack(side="left", padx=2, pady=5)
        ctk.CTkButton(buttons_frame, text="Дублировать", command=self.duplicate_profile, width=100).pack(side="left", padx=2, pady=5)
        ctk.CTkButton(buttons_frame, text="Удалить", command=self.delete_profile, width=100).pack(side="left", padx=2, pady=5)

        right_frame = ctk.CTkFrame(self.parent)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 10), pady=10)

        ctk.CTkLabel(right_frame, text="Редактирование профиля", font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 10))

        self.edit_frame = ctk.CTkScrollableFrame(right_frame)
        self.edit_frame.pack(fill="both", expand=True)

        self.profile_name_entry = None
        self.format_combo = None
        self.use_cookies_var = None
        self.write_subs_var = None
        self.sub_lang_entry = None
        self.embed_thumbnail_var = None
        self.write_metadata_var = None
        self.extract_audio_var = None

        self.create_edit_form()

    def create_edit_form(self):
        for widget in self.edit_frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.edit_frame, text="Название профиля:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
        self.profile_name_entry = ctk.CTkEntry(self.edit_frame, placeholder_text="Название")
        self.profile_name_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.edit_frame, text="Формат:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
        self.format_combo = ctk.CTkComboBox(self.edit_frame, values=["best", "bestaudio"])
        self.format_combo.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(self.edit_frame, text="Качество:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
        self.quality_combo = ctk.CTkComboBox(self.edit_frame, values=["best", "1080p", "720p", "480p"])
        self.quality_combo.pack(fill="x", pady=(0, 10))

        self.use_cookies_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.edit_frame, text="Использовать cookies Firefox", variable=self.use_cookies_var).pack(anchor="w", pady=5)

        self.write_subs_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.edit_frame, text="Загружать субтитры", variable=self.write_subs_var).pack(anchor="w", pady=5)

        ctk.CTkLabel(self.edit_frame, text="Язык субтитров:", font=("Arial", 12)).pack(anchor="w", pady=(5, 2))
        self.sub_lang_entry = ctk.CTkEntry(self.edit_frame, placeholder_text="ru")
        self.sub_lang_entry.pack(fill="x", pady=(0, 10))

        self.embed_thumbnail_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.edit_frame, text="Встроить миниатюру", variable=self.embed_thumbnail_var).pack(anchor="w", pady=5)

        self.write_metadata_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.edit_frame, text="Добавить метаданные", variable=self.write_metadata_var).pack(anchor="w", pady=5)

        self.extract_audio_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.edit_frame, text="Извлечь только аудио", variable=self.extract_audio_var).pack(anchor="w", pady=5)

        ctk.CTkButton(self.edit_frame, text="Сохранить профиль", command=self.save_profile, height=40).pack(fill="x", pady=(20, 0))

    def refresh_profiles(self):
        for widget in self.profiles_list.winfo_children():
            widget.destroy()

        profiles = self.config_manager.get_all_profiles()

        for profile_id, profile_data in profiles.items():
            profile_btn = ctk.CTkButton(
                self.profiles_list,
                text=profile_data.get('name', profile_id),
                command=lambda pid=profile_id: self.select_profile(pid),
                anchor="w"
            )
            profile_btn.pack(fill="x", pady=2)

    def select_profile(self, profile_id):
        self.selected_profile_id = profile_id
        profile = self.config_manager.get_profile(profile_id)

        if profile:
            self.profile_name_entry.delete(0, 'end')
            self.profile_name_entry.insert(0, profile.get('name', ''))

            self.format_combo.set(profile.get('format', 'best'))
            self.quality_combo.set(profile.get('quality', 'best'))
            self.use_cookies_var.set(profile.get('use_cookies', False))
            self.write_subs_var.set(profile.get('write_subs', False))

            self.sub_lang_entry.delete(0, 'end')
            self.sub_lang_entry.insert(0, profile.get('sub_lang', 'ru'))

            self.embed_thumbnail_var.set(profile.get('embed_thumbnail', False))
            self.write_metadata_var.set(profile.get('write_metadata', True))
            self.extract_audio_var.set(profile.get('extract_audio', False))

    def create_profile(self):
        dialog = ctk.CTkInputDialog(text="Введите название нового профиля:", title="Создать профиль")
        profile_name = dialog.get_input()

        if profile_name:
            settings = {
                'format': 'best',
                'quality': 'best',
                'use_cookies': False,
                'write_subs': False,
                'sub_lang': 'ru',
                'embed_thumbnail': False,
                'write_metadata': True,
                'extract_audio': False
            }

            if self.config_manager.create_profile(profile_name, settings):
                self.refresh_profiles()
                if self.on_profiles_changed:
                    self.on_profiles_changed()

                profile_id = profile_name.lower().replace(' ', '_')
                self.select_profile(profile_id)

    def save_profile(self):
        if not self.selected_profile_id:
            return

        profile_name = self.profile_name_entry.get().strip()
        if not profile_name:
            return

        settings = {
            'name': profile_name,
            'format': self.format_combo.get(),
            'quality': self.quality_combo.get(),
            'use_cookies': self.use_cookies_var.get(),
            'write_subs': self.write_subs_var.get(),
            'sub_lang': self.sub_lang_entry.get() or 'ru',
            'embed_thumbnail': self.embed_thumbnail_var.get(),
            'write_metadata': self.write_metadata_var.get(),
            'extract_audio': self.extract_audio_var.get()
        }

        if self.config_manager.update_profile(self.selected_profile_id, settings):
            self.refresh_profiles()
            if self.on_profiles_changed:
                self.on_profiles_changed()

            success_label = ctk.CTkLabel(self.edit_frame, text="Профиль сохранен!", font=("Arial", 12), text_color="green")
            success_label.pack(pady=10)
            self.parent.after(2000, success_label.destroy)

    def duplicate_profile(self):
        if not self.selected_profile_id:
            return

        dialog = ctk.CTkInputDialog(text="Введите название для копии профиля:", title="Дублировать профиль")
        new_name = dialog.get_input()

        if new_name:
            if self.config_manager.duplicate_profile(self.selected_profile_id, new_name):
                self.refresh_profiles()
                if self.on_profiles_changed:
                    self.on_profiles_changed()

    def delete_profile(self):
        if not self.selected_profile_id or self.selected_profile_id == 'default':
            return

        if self.config_manager.delete_profile(self.selected_profile_id):
            self.selected_profile_id = None
            self.refresh_profiles()
            self.create_edit_form()
            if self.on_profiles_changed:
                self.on_profiles_changed()
