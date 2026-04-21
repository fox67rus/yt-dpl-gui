import customtkinter as ctk
from gui.download_tab import DownloadTab
from gui.queue_tab import QueueTab
from gui.settings_tab import SettingsTab
from gui.profiles_tab import ProfilesTab
from core.config_manager import ConfigManager
from core.queue_manager import DownloadQueue


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("yt-dlp GUI")
        self.geometry("1000x700")

        self.config_manager = ConfigManager()
        self.download_queue = DownloadQueue(
            max_concurrent=self.config_manager.get('max_concurrent_downloads', 3),
            status_callback=self.on_queue_status_change
        )

        theme = self.config_manager.get('theme', 'dark')
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.download_tab_frame = self.tabview.add("Загрузка")
        self.queue_tab_frame = self.tabview.add("Очередь")
        self.settings_tab_frame = self.tabview.add("Настройки")
        self.profiles_tab_frame = self.tabview.add("Профили")

        self.download_tab = DownloadTab(
            self.download_tab_frame,
            self.config_manager,
            self.download_queue
        )

        self.queue_tab = QueueTab(
            self.queue_tab_frame,
            self.download_queue
        )

        self.settings_tab = SettingsTab(
            self.settings_tab_frame,
            self.config_manager,
            self.on_settings_changed
        )

        self.profiles_tab = ProfilesTab(
            self.profiles_tab_frame,
            self.config_manager,
            self.on_profiles_changed
        )

    def on_queue_status_change(self):
        """Обработчик изменения статуса очереди"""
        self.queue_tab.refresh_queue()

    def on_settings_changed(self):
        """Обработчик изменения настроек"""
        theme = self.config_manager.get('theme', 'dark')
        ctk.set_appearance_mode(theme)

        max_concurrent = self.config_manager.get('max_concurrent_downloads', 3)
        self.download_queue.set_max_concurrent(max_concurrent)

    def on_profiles_changed(self):
        """Обработчик изменения профилей"""
        self.download_tab.refresh_profiles()

    def run(self):
        """Запустить приложение"""
        self.mainloop()
