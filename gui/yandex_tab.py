import os
import threading
import customtkinter as ctk
from tkinter import filedialog
from typing import Optional

from core.config_manager import ConfigManager
from core.yandex_downloader import YandexDownloader


class YandexTab:
    def __init__(self, parent, config_manager: ConfigManager):
        self.parent = parent
        self.config_manager = config_manager
        self.downloader: Optional[YandexDownloader] = None
        self.current_info = None

        self.setup_ui()
        self._init_downloader()

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------

    def _init_downloader(self):
        token = self.config_manager.get('yandex_token', '')
        if token:
            self.downloader = YandexDownloader(token, progress_callback=self.on_progress)
            self.token_status_label.configure(text="Токен задан", text_color="green")
        else:
            self.token_status_label.configure(
                text="Токен не задан — настройте в разделе Настройки → Яндекс Музыка",
                text_color="orange"
            )

    def refresh_token(self):
        """Вызывается из MainWindow при изменении настроек."""
        token = self.config_manager.get('yandex_token', '')
        if self.downloader:
            self.downloader.update_token(token)
        elif token:
            self.downloader = YandexDownloader(token, progress_callback=self.on_progress)

        if token:
            self.token_status_label.configure(text="Токен задан", text_color="green")
        else:
            self.token_status_label.configure(
                text="Токен не задан — настройте в разделе Настройки → Яндекс Музыка",
                text_color="orange"
            )

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def setup_ui(self):
        main_frame = ctk.CTkScrollableFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Token status
        self.token_status_label = ctk.CTkLabel(main_frame, text="", font=("Arial", 11))
        self.token_status_label.pack(anchor="w", pady=(0, 10))

        # URL
        ctk.CTkLabel(main_frame, text="Ссылка на Яндекс Музыку:", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 5))

        url_frame = ctk.CTkFrame(main_frame)
        url_frame.pack(fill="x", pady=(0, 10))

        self.url_entry = ctk.CTkEntry(url_frame, placeholder_text="Трек, альбом, плейлист или артист")
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=10)
        self.url_entry.bind("<Control-v>", self._paste_url)
        self.url_entry.bind("<Control-V>", self._paste_url)
        self.url_entry.bind("<Control-Key>", self._handle_ctrl)

        self.info_btn = ctk.CTkButton(url_frame, text="Информация", command=self.fetch_info, width=120)
        self.info_btn.pack(side="right", padx=(5, 10), pady=10)

        # Info preview
        self.info_frame = ctk.CTkFrame(main_frame)
        self.info_frame.pack(fill="x", pady=(0, 10))
        self.info_frame.pack_forget()

        self.info_label = ctk.CTkLabel(self.info_frame, text="", font=("Arial", 12), justify="left")
        self.info_label.pack(padx=10, pady=10, anchor="w")

        # Options
        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=(0, 10))

        left = ctk.CTkFrame(options_frame, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(left, text="Формат:", font=("Arial", 12)).pack(anchor="w", pady=(0, 3))
        self.codec_combo = ctk.CTkComboBox(left, values=["mp3", "aac", "flac"])
        self.codec_combo.set("mp3")
        self.codec_combo.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(left, text="Качество (kbps):", font=("Arial", 12)).pack(anchor="w", pady=(0, 3))
        self.bitrate_combo = ctk.CTkComboBox(left, values=["128", "192", "320"])
        self.bitrate_combo.set("192")
        self.bitrate_combo.pack(fill="x", pady=(0, 10))

        right = ctk.CTkFrame(options_frame, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(right, text="Папка сохранения:", font=("Arial", 12)).pack(anchor="w", pady=(0, 3))
        path_frame = ctk.CTkFrame(right, fg_color="transparent")
        path_frame.pack(fill="x", pady=(0, 10))

        default_path = self.config_manager.get('yandex_download_path',
                       self.config_manager.get('default_download_path', './downloads'))
        self.path_entry = ctk.CTkEntry(path_frame)
        self.path_entry.insert(0, default_path)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(path_frame, text="Обзор", command=self.browse_folder, width=80).pack(side="right")

        # Buttons
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", pady=(0, 10))

        self.download_btn = ctk.CTkButton(btn_frame, text="Загрузить", command=self.download_now, height=40)
        self.download_btn.pack(fill="x", padx=10, pady=10)

        # Progress
        self.progress_frame = ctk.CTkFrame(main_frame)
        self.progress_frame.pack(fill="x", pady=(0, 10))
        self.progress_frame.pack_forget()

        self.progress_label = ctk.CTkLabel(self.progress_frame, text="", font=("Arial", 12))
        self.progress_label.pack(padx=10, pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=(0, 10))
        self.progress_bar.set(0)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _paste_url(self, event=None):
        try:
            text = self.url_entry.clipboard_get()
            if text:
                self.url_entry.delete(0, 'end')
                self.url_entry.insert(0, text.strip())
            return "break"
        except Exception:
            return "break"

    def _handle_ctrl(self, event):
        if event.keycode == 86:
            return self._paste_url(event)
        return None

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, 'end')
            self.path_entry.insert(0, folder)

    def _check_token(self) -> bool:
        if not self.downloader or not self.config_manager.get('yandex_token', ''):
            self.info_frame.pack(fill="x", pady=(0, 10))
            self.info_label.configure(
                text="Токен не задан.\nПерейдите в Настройки → Яндекс Музыка и введите токен."
            )
            return False
        return True

    # ------------------------------------------------------------------
    # Info fetch
    # ------------------------------------------------------------------

    def fetch_info(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        if not self._check_token():
            return

        self.info_btn.configure(state="disabled", text="Загрузка...")

        def worker():
            try:
                info = self.downloader.get_info(url)
                self.parent.after(0, lambda: self._show_info(info))
            except Exception as e:
                self.parent.after(0, lambda: self._show_error(str(e)))
            finally:
                self.parent.after(0, lambda: self.info_btn.configure(state="normal", text="Информация"))

        threading.Thread(target=worker, daemon=True).start()

    def _show_info(self, info: dict):
        self.current_info = info
        self.info_frame.pack(fill="x", pady=(0, 10))

        dur_ms = info.get('duration_ms', 0)
        dur_s = dur_ms // 1000
        dur_str = f"{dur_s // 60}:{dur_s % 60:02d}" if dur_s else "N/A"

        count = info.get('count', 1)
        if count == 1:
            text = (f"Трек: {info.get('artist', '')} — {info.get('title', '')}\n"
                    f"Длительность: {dur_str}")
        else:
            label = info.get('type_label', '')
            text = (f"{label}: {info.get('artist', '')} — {info.get('title', '')}\n"
                    f"Треков: {count}  |  Общая длительность: {dur_str}")

        self.info_label.configure(text=text)

    def _show_error(self, msg: str):
        self.info_frame.pack(fill="x", pady=(0, 10))
        self.info_label.configure(text=f"Ошибка: {msg}")

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def _get_options(self) -> dict:
        output_dir = self.path_entry.get().strip()
        self.config_manager.set('yandex_download_path', output_dir)
        return {
            'output_path': output_dir,
            'codec': self.codec_combo.get(),
            'bitrate': int(self.bitrate_combo.get()),
        }

    def download_now(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        if not self._check_token():
            return

        options = self._get_options()

        self.progress_frame.pack(fill="x", pady=(0, 10))
        self.progress_bar.set(0)
        self.progress_label.configure(text="Подготовка...")
        self.download_btn.configure(state="disabled")

        def done(success, error):
            self.parent.after(0, lambda: self._on_done(success, error))

        self.downloader.download_async(url, options, done)

    def _on_done(self, success: bool, error: Optional[str]):
        self.download_btn.configure(state="normal")
        if success:
            self.progress_label.configure(text="Готово!")
            self.progress_bar.set(1.0)
        else:
            self.progress_label.configure(text=f"Ошибка: {error}")

    # ------------------------------------------------------------------
    # Progress callback (called from background thread)
    # ------------------------------------------------------------------

    def on_progress(self, d: dict):
        status = d.get('status')
        if status == 'downloading':
            current = d.get('current', 1)
            total = d.get('total', 1)
            title = d.get('title', '')
            progress = current / total if total else 0
            text = f"[{current}/{total}] {title}"
            self.parent.after(0, lambda: self.progress_bar.set(progress))
            self.parent.after(0, lambda: self.progress_label.configure(text=text))
        elif status == 'finished':
            total = d.get('total', 0)
            self.parent.after(0, lambda: self.progress_label.configure(text=f"Готово! Скачано треков: {total}"))
            self.parent.after(0, lambda: self.progress_bar.set(1.0))
