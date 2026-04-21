import customtkinter as ctk
from tkinter import filedialog
from core.config_manager import ConfigManager
from core.firefox_cookies import get_firefox_status


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
                    font=("Arial", 10), text_color="gray").pack(anchor="w", padx=10, pady=(2, 10))

        save_btn = ctk.CTkButton(main_frame, text="Сохранить настройки", command=self.save_settings, height=40)
        save_btn.pack(fill="x", pady=(10, 0))

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
