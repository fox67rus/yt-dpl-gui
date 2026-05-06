import os
import customtkinter as ctk
from tkinter import filedialog
from core.config_manager import ConfigManager
from core.firefox_cookies import get_firefox_status, export_cookies_to_file
from utils.helpers import find_ffmpeg


class SettingsTab:
    def __init__(self, parent, config_manager: ConfigManager, on_settings_changed):
        self.parent = parent
        self.config_manager = config_manager
        self.on_settings_changed = on_settings_changed

        self.setup_ui()

    def setup_ui(self):
        main_frame = ctk.CTkScrollableFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(main_frame, text="Общие настройки", font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 10))

        general_frame = ctk.CTkFrame(main_frame)
        general_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(general_frame, text="Папка загрузок по умолчанию:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=(10, 5))

        path_frame = ctk.CTkFrame(general_frame, fg_color="transparent")
        path_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.download_path_entry = ctk.CTkEntry(path_frame)
        self.download_path_entry.insert(0, self.config_manager.get('default_download_path', './downloads'))
        self.download_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(path_frame, text="Обзор", command=self.browse_download_folder, width=80).pack(side="right")

        ctk.CTkLabel(general_frame, text="Шаблон имени файла:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=(10, 5))

        self.filename_template_entry = ctk.CTkEntry(general_frame, placeholder_text="%(title)s.%(ext)s")
        self.filename_template_entry.insert(0, self.config_manager.get('filename_template', '%(title)s.%(ext)s'))
        self.filename_template_entry.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(general_frame, text="Тема интерфейса:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=(10, 5))

        self.theme_combo = ctk.CTkComboBox(general_frame, values=["dark", "light", "system"])
        self.theme_combo.set(self.config_manager.get('theme', 'dark'))
        self.theme_combo.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(main_frame, text="Настройки загрузки", font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 10))

        download_frame = ctk.CTkFrame(main_frame)
        download_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(download_frame, text="Максимальное количество параллельных загрузок:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=(10, 5))

        concurrent_frame = ctk.CTkFrame(download_frame, fg_color="transparent")
        concurrent_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.concurrent_slider = ctk.CTkSlider(concurrent_frame, from_=1, to=10, number_of_steps=9, command=self.on_concurrent_changed)
        self.concurrent_slider.set(self.config_manager.get('max_concurrent_downloads', 3))
        self.concurrent_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.concurrent_label = ctk.CTkLabel(concurrent_frame, text=str(self.config_manager.get('max_concurrent_downloads', 3)))
        self.concurrent_label.pack(side="right")

        ctk.CTkLabel(download_frame, text="Количество повторов при ошибке:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=(10, 5))

        self.retries_entry = ctk.CTkEntry(download_frame, placeholder_text="3")
        self.retries_entry.insert(0, str(self.config_manager.get('max_retries', 3)))
        self.retries_entry.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(download_frame, text="Таймаут соединения (секунды):", font=("Arial", 12)).pack(anchor="w", padx=10, pady=(10, 5))

        self.timeout_entry = ctk.CTkEntry(download_frame, placeholder_text="30")
        self.timeout_entry.insert(0, str(self.config_manager.get('socket_timeout', 30)))
        self.timeout_entry.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(main_frame, text="FFmpeg", font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 10))

        ffmpeg_frame = ctk.CTkFrame(main_frame)
        ffmpeg_frame.pack(fill="x", pady=(0, 20))

        configured_ffmpeg = self.config_manager.get('ffmpeg_location', '')
        ffmpeg_result = find_ffmpeg(configured_ffmpeg)
        if ffmpeg_result is None:
            ffmpeg_status_text, ffmpeg_status_color = "Найден (системный PATH)", "green"
        elif ffmpeg_result:
            ffmpeg_status_text, ffmpeg_status_color = f"Найден: {ffmpeg_result}", "green"
        else:
            ffmpeg_status_text, ffmpeg_status_color = "Не найден — метаданные, аудио и миниатюры не будут работать", "red"

        self.ffmpeg_status_label = ctk.CTkLabel(
            ffmpeg_frame, text=ffmpeg_status_text,
            font=("Arial", 11), text_color=ffmpeg_status_color
        )
        self.ffmpeg_status_label.pack(anchor="w", padx=10, pady=(10, 5))

        ctk.CTkLabel(ffmpeg_frame, text="Путь к ffmpeg (папка или файл):", font=("Arial", 12)).pack(anchor="w", padx=10, pady=(5, 2))

        ffmpeg_path_frame = ctk.CTkFrame(ffmpeg_frame, fg_color="transparent")
        ffmpeg_path_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.ffmpeg_path_entry = ctk.CTkEntry(ffmpeg_path_frame, placeholder_text="Оставьте пустым для автоопределения")
        self.ffmpeg_path_entry.insert(0, configured_ffmpeg)
        self.ffmpeg_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ctk.CTkButton(ffmpeg_path_frame, text="Обзор", command=self.browse_ffmpeg, width=80).pack(side="right")

        ctk.CTkLabel(main_frame, text="Firefox Cookies", font=("Arial", 16, "bold")).pack(anchor="w", pady=(10, 10))

        cookies_frame = ctk.CTkFrame(main_frame)
        cookies_frame.pack(fill="x", pady=(0, 20))

        firefox_status = get_firefox_status()

        status_text = "Найдены" if firefox_status['available'] else "Не найдены"
        status_color = "green" if firefox_status['available'] else "red"

        ctk.CTkLabel(cookies_frame, text=f"Статус: {status_text}", font=("Arial", 12, "bold"),
                    text_color=status_color).pack(anchor="w", padx=10, pady=(10, 5))

        ctk.CTkLabel(cookies_frame, text=f"Путь к профилю: {firefox_status['profile_path']}",
                    font=("Arial", 10), text_color="gray").pack(anchor="w", padx=10, pady=2)

        ctk.CTkLabel(cookies_frame, text=f"Путь к cookies: {firefox_status['cookies_path']}",
                    font=("Arial", 10), text_color="gray").pack(anchor="w", padx=10, pady=(2, 5))

        export_row = ctk.CTkFrame(cookies_frame, fg_color="transparent")
        export_row.pack(fill="x", padx=10, pady=(0, 10))

        self.export_btn = ctk.CTkButton(
            export_row,
            text="Экспортировать куки в файл",
            command=self.export_cookies,
            state="normal" if firefox_status['available'] else "disabled",
            width=220,
        )
        self.export_btn.pack(side="left", padx=(0, 10))

        self.export_status_label = ctk.CTkLabel(export_row, text="", font=("Arial", 11))
        self.export_status_label.pack(side="left", fill="x", expand=True)

        save_btn = ctk.CTkButton(main_frame, text="Сохранить настройки", command=self.save_settings, height=40)
        save_btn.pack(fill="x", pady=(10, 0))

    def export_cookies(self):
        saved_path = self.config_manager.get('last_cookies_file', '')
        if saved_path:
            output_path = saved_path
        else:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_path = os.path.join(root_dir, 'cookies.txt')

        self.export_btn.configure(state="disabled", text="Экспорт...")
        self.export_status_label.configure(text="", text_color="gray")

        def do_export():
            success, message = export_cookies_to_file(output_path)
            if success and not self.config_manager.get('last_cookies_file'):
                self.config_manager.set('last_cookies_file', output_path)
            self.parent.after(0, lambda: self._on_export_done(success, message))

        import threading
        threading.Thread(target=do_export, daemon=True).start()

    def _on_export_done(self, success: bool, message: str):
        self.export_btn.configure(state="normal", text="Экспортировать куки в файл")
        color = "green" if success else "red"
        self.export_status_label.configure(text=message, text_color=color)

    def browse_ffmpeg(self):
        path = filedialog.askopenfilename(
            title="Выберите ffmpeg",
            filetypes=[("ffmpeg", "ffmpeg ffmpeg.exe"), ("Все файлы", "*.*")]
        )
        if path:
            self.ffmpeg_path_entry.delete(0, 'end')
            self.ffmpeg_path_entry.insert(0, path)

    def browse_download_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_path_entry.delete(0, 'end')
            self.download_path_entry.insert(0, folder)

    def on_concurrent_changed(self, value):
        self.concurrent_label.configure(text=str(int(value)))

    def save_settings(self):
        self.config_manager.set('default_download_path', self.download_path_entry.get())
        self.config_manager.set('filename_template', self.filename_template_entry.get())
        self.config_manager.set('theme', self.theme_combo.get())
        self.config_manager.set('max_concurrent_downloads', int(self.concurrent_slider.get()))
        self.config_manager.set('ffmpeg_location', self.ffmpeg_path_entry.get().strip())

        ffmpeg_result = find_ffmpeg(self.ffmpeg_path_entry.get().strip())
        if ffmpeg_result is None:
            self.ffmpeg_status_label.configure(text="Найден (системный PATH)", text_color="green")
        elif ffmpeg_result:
            self.ffmpeg_status_label.configure(text=f"Найден: {ffmpeg_result}", text_color="green")
        else:
            self.ffmpeg_status_label.configure(text="Не найден — метаданные, аудио и миниатюры не будут работать", text_color="red")

        try:
            self.config_manager.set('max_retries', int(self.retries_entry.get()))
        except ValueError:
            pass

        try:
            self.config_manager.set('socket_timeout', int(self.timeout_entry.get()))
        except ValueError:
            pass

        if self.on_settings_changed:
            self.on_settings_changed()

        success_label = ctk.CTkLabel(self.parent, text="Настройки сохранены!", font=("Arial", 12), text_color="green")
        success_label.place(relx=0.5, rely=0.95, anchor="center")
        self.parent.after(2000, success_label.destroy)
