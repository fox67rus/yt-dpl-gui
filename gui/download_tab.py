import customtkinter as ctk
from tkinter import filedialog
import os
import threading
from typing import Optional
from PIL import Image
import requests
from io import BytesIO
from core.config_manager import ConfigManager
from core.queue_manager import DownloadQueue, DownloadItem
from core.downloader import YTDLPDownloader
from core.firefox_cookies import check_firefox_cookies_available


class DownloadTab:
    def __init__(self, parent, config_manager: ConfigManager, download_queue: DownloadQueue):
        self.parent = parent
        self.config_manager = config_manager
        self.download_queue = download_queue
        self.downloader = YTDLPDownloader(progress_callback=self.on_progress)
        self.current_video_info = None

        self.setup_ui()

    def setup_ui(self):
        main_frame = ctk.CTkScrollableFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(main_frame, text="URL видео:", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 5))

        url_frame = ctk.CTkFrame(main_frame)
        url_frame.pack(fill="x", pady=(0, 10))

        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="Вставьте ссылку на видео")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)

        # Биндинги для вставки
        self.url_entry.bind("<Control-v>", self.paste_url)
        self.url_entry.bind("<Control-V>", self.paste_url)
        self.url_entry.bind("<<Paste>>", self.paste_url)
        # Добавляем обработку любых Control комбинаций
        self.url_entry.bind("<Control-Key>", self.handle_control_key)

        self.preview_btn = ctk.CTkButton(url_frame, text="Предпросмотр", command=self.preview_video, width=120)
        self.preview_btn.pack(side="right", padx=(5, 10), pady=10)

        self.preview_frame = ctk.CTkFrame(main_frame)
        self.preview_frame.pack(fill="x", pady=(0, 10))
        self.preview_frame.pack_forget()

        self.preview_label = ctk.CTkLabel(self.preview_frame, text="", font=("Arial", 12))
        self.preview_label.pack(padx=10, pady=10)

        settings_frame = ctk.CTkFrame(main_frame)
        settings_frame.pack(fill="x", pady=(0, 10))

        left_col = ctk.CTkFrame(settings_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(left_col, text="Профиль:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
        self.profile_combo = ctk.CTkComboBox(left_col, values=self.get_profile_names(), command=self.on_profile_selected)
        self.profile_combo.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(left_col, text="Формат:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
        self.format_combo = ctk.CTkComboBox(left_col, values=["Лучшее видео", "Лучшее аудио", "1080p", "720p", "480p"])
        self.format_combo.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(left_col, text="Путь сохранения:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
        path_frame = ctk.CTkFrame(left_col, fg_color="transparent")
        path_frame.pack(fill="x", pady=(0, 10))

        default_path = self.config_manager.get('default_download_path', './downloads')
        self.path_entry = ctk.CTkEntry(path_frame)
        self.path_entry.insert(0, default_path)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(path_frame, text="Обзор", command=self.browse_folder, width=80).pack(side="right")

        right_col = ctk.CTkFrame(settings_frame, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.use_cookies_var = ctk.BooleanVar(value=False)
        cookies_available = check_firefox_cookies_available()
        cookies_text = "Использовать cookies Firefox"
        if not cookies_available:
            cookies_text += " (не найдены)"

        self.cookies_check = ctk.CTkCheckBox(right_col, text=cookies_text, variable=self.use_cookies_var)
        self.cookies_check.pack(anchor="w", pady=5)
        if not cookies_available:
            self.cookies_check.configure(state="disabled")

        self.advanced_frame = ctk.CTkFrame(main_frame)
        self.advanced_frame.pack(fill="x", pady=(0, 10))

        self.show_advanced_var = ctk.BooleanVar(value=False)
        advanced_toggle = ctk.CTkCheckBox(
            self.advanced_frame,
            text="Расширенные настройки",
            variable=self.show_advanced_var,
            command=self.toggle_advanced
        )
        advanced_toggle.pack(anchor="w", padx=10, pady=10)

        self.advanced_options = ctk.CTkFrame(self.advanced_frame)
        self.advanced_options.pack(fill="x", padx=10, pady=(0, 10))
        self.advanced_options.pack_forget()

        self.write_subs_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.advanced_options, text="Загрузить субтитры", variable=self.write_subs_var).pack(anchor="w", pady=5)

        ctk.CTkLabel(self.advanced_options, text="Язык субтитров:").pack(anchor="w", pady=(5, 2))
        self.sub_lang_entry = ctk.CTkEntry(self.advanced_options, placeholder_text="ru")
        self.sub_lang_entry.pack(fill="x", pady=(0, 10))

        self.embed_thumbnail_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(self.advanced_options, text="Встроить миниатюру", variable=self.embed_thumbnail_var).pack(anchor="w", pady=5)

        self.write_metadata_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.advanced_options, text="Добавить метаданные", variable=self.write_metadata_var).pack(anchor="w", pady=5)

        buttons_frame = ctk.CTkFrame(main_frame)
        buttons_frame.pack(fill="x", pady=(0, 10))

        self.download_btn = ctk.CTkButton(buttons_frame, text="Загрузить сейчас", command=self.download_now, height=40)
        self.download_btn.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)

        self.queue_btn = ctk.CTkButton(buttons_frame, text="Добавить в очередь", command=self.add_to_queue, height=40)
        self.queue_btn.pack(side="right", fill="x", expand=True, padx=(5, 10), pady=10)

        self.progress_frame = ctk.CTkFrame(main_frame)
        self.progress_frame.pack(fill="x", pady=(0, 10))
        self.progress_frame.pack_forget()

        self.progress_label = ctk.CTkLabel(self.progress_frame, text="Загрузка...", font=("Arial", 12))
        self.progress_label.pack(padx=10, pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.progress_bar.set(0)

    def get_profile_names(self):
        profiles = self.config_manager.get_profile_list()
        return [p['name'] for p in profiles]

    def on_profile_selected(self, profile_name):
        profiles = self.config_manager.get_all_profiles()
        for profile_id, profile_data in profiles.items():
            if profile_data.get('name') == profile_name:
                self.apply_profile(profile_data)
                break

    def apply_profile(self, profile):
        format_map = {
            'best': 'Лучшее видео',
            'bestaudio': 'Лучшее аудио',
            'bestvideo+bestaudio/best': 'Лучшее видео',
            'bestaudio/best': 'Лучшее аудио',
        }
        self.format_combo.set(format_map.get(profile.get('format', 'best'), 'Лучшее видео'))
        self.use_cookies_var.set(profile.get('use_cookies', False))
        self.write_subs_var.set(profile.get('write_subs', False))
        self.sub_lang_entry.delete(0, 'end')
        self.sub_lang_entry.insert(0, profile.get('sub_lang', 'ru'))
        self.embed_thumbnail_var.set(profile.get('embed_thumbnail', False))
        self.write_metadata_var.set(profile.get('write_metadata', True))

    def toggle_advanced(self):
        if self.show_advanced_var.get():
            self.advanced_options.pack(fill="x", padx=10, pady=(0, 10))
        else:
            self.advanced_options.pack_forget()

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, folder)

    def paste_url(self, event=None):
        """Обработка вставки URL независимо от раскладки клавиатуры"""
        try:
            # Получаем текст из буфера обмена
            clipboard_text = self.url_entry.clipboard_get()
            if clipboard_text:
                # Очищаем поле и вставляем текст
                self.url_entry.delete(0, 'end')
                self.url_entry.insert(0, clipboard_text.strip())
            return "break"  # Останавливаем дальнейшую обработку события
        except Exception as e:
            print(f"Ошибка вставки: {e}")
            return "break"

    def handle_control_key(self, event):
        """Обработка Control+клавиша для перехвата Ctrl+V на русской раскладке"""
        # Проверяем keycode для клавиши V (одинаковый для любой раскладки)
        if event.keycode == 86:  # keycode для клавиши V/М
            return self.paste_url(event)
        return None

    def preview_video(self):
        url = self.url_entry.get().strip()
        if not url:
            return

        self.preview_btn.configure(state="disabled", text="Загрузка...")

        def fetch_info():
            try:
                info = self.downloader.get_video_info(url, self.use_cookies_var.get())
                self.current_video_info = info
                self.parent.after(0, lambda: self.display_preview(info))
            except Exception as e:
                self.parent.after(0, lambda: self.show_error(str(e)))
            finally:
                self.parent.after(0, lambda: self.preview_btn.configure(state="normal", text="Предпросмотр"))

        threading.Thread(target=fetch_info, daemon=True).start()

    def display_preview(self, info):
        self.preview_frame.pack(fill="x", pady=(0, 10))

        duration = info.get('duration', 0)
        duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "N/A"
        filesize = info.get('filesize', 0)
        filesize_str = f"{filesize / (1024*1024):.1f} MB" if filesize else "N/A"

        preview_text = f"Название: {info.get('title', 'N/A')}\n"
        preview_text += f"Длительность: {duration_str}\n"
        preview_text += f"Размер: {filesize_str}\n"
        preview_text += f"Автор: {info.get('uploader', 'N/A')}"

        self.preview_label.configure(text=preview_text)

    def show_error(self, error_msg):
        self.preview_frame.pack(fill="x", pady=(0, 10))
        self.preview_label.configure(text=f"Ошибка: {error_msg}")

    def get_download_options(self):
        format_map = {
            'Лучшее видео': 'best',
            'Лучшее аудио': 'bestaudio',
            '1080p': 'best[height<=1080]',
            '720p': 'best[height<=720]',
            '480p': 'best[height<=480]',
        }

        download_path = self.path_entry.get().strip()
        if not os.path.exists(download_path):
            os.makedirs(download_path, exist_ok=True)

        filename_template = self.config_manager.get('filename_template', '%(title)s.%(ext)s')
        output_path = os.path.join(download_path, filename_template)

        return {
            'format': format_map.get(self.format_combo.get(), 'best'),
            'output_path': output_path,
            'use_cookies': self.use_cookies_var.get(),
            'write_subs': self.write_subs_var.get(),
            'sub_lang': self.sub_lang_entry.get() or 'ru',
            'embed_thumbnail': self.embed_thumbnail_var.get(),
            'write_metadata': self.write_metadata_var.get(),
            'title': self.current_video_info.get('title', 'Unknown') if self.current_video_info else 'Unknown'
        }

    def download_now(self):
        url = self.url_entry.get().strip()
        if not url:
            return

        options = self.get_download_options()

        self.progress_frame.pack(fill="x", pady=(0, 10))
        self.progress_bar.set(0)
        self.download_btn.configure(state="disabled")
        self.queue_btn.configure(state="disabled")

        def completion_callback(success, error):
            self.parent.after(0, lambda: self.on_download_complete(success, error))

        self.downloader.download_async(url, options, completion_callback)

    def add_to_queue(self):
        url = self.url_entry.get().strip()
        if not url:
            return

        options = self.get_download_options()
        item = DownloadItem(url, options)
        self.download_queue.add_to_queue(item)

        self.url_entry.delete(0, 'end')
        self.preview_frame.pack_forget()

    def on_progress(self, d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)

            if total > 0:
                progress = downloaded / total
                self.parent.after(0, lambda: self.progress_bar.set(progress))

                speed = d.get('_speed_str', '')
                eta = d.get('_eta_str', '')
                text = f"Загрузка... {speed} ETA: {eta}"
                self.parent.after(0, lambda: self.progress_label.configure(text=text))

    def on_download_complete(self, success, error):
        self.download_btn.configure(state="normal")
        self.queue_btn.configure(state="normal")

        if success:
            self.progress_label.configure(text="Загрузка завершена!")
            self.progress_bar.set(1.0)
        else:
            self.progress_label.configure(text=f"Ошибка: {error}")

    def refresh_profiles(self):
        self.profile_combo.configure(values=self.get_profile_names())
