import customtkinter as ctk
from core.queue_manager import DownloadQueue


class QueueTab:
    def __init__(self, parent, download_queue: DownloadQueue):
        self.parent = parent
        self.download_queue = download_queue
        self.item_widgets = {}

        self.setup_ui()

    def setup_ui(self):
        control_frame = ctk.CTkFrame(self.parent)
        control_frame.pack(fill="x", padx=10, pady=10)

        self.start_btn = ctk.CTkButton(control_frame, text="Запустить очередь", command=self.start_queue, width=150)
        self.start_btn.pack(side="left", padx=5, pady=10)

        self.stop_btn = ctk.CTkButton(control_frame, text="Приостановить", command=self.stop_queue, width=150)
        self.stop_btn.pack(side="left", padx=5, pady=10)
        self.stop_btn.configure(state="disabled")

        self.clear_btn = ctk.CTkButton(control_frame, text="Очистить завершенные", command=self.clear_completed, width=180)
        self.clear_btn.pack(side="left", padx=5, pady=10)

        ctk.CTkLabel(control_frame, text="Параллельных загрузок:").pack(side="left", padx=(20, 5), pady=10)

        self.concurrent_slider = ctk.CTkSlider(control_frame, from_=1, to=5, number_of_steps=4, command=self.on_concurrent_changed)
        self.concurrent_slider.set(self.download_queue.max_concurrent)
        self.concurrent_slider.pack(side="left", padx=5, pady=10)

        self.concurrent_label = ctk.CTkLabel(control_frame, text=str(self.download_queue.max_concurrent))
        self.concurrent_label.pack(side="left", padx=5, pady=10)

        self.queue_frame = ctk.CTkScrollableFrame(self.parent)
        self.queue_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.empty_label = ctk.CTkLabel(self.queue_frame, text="Очередь пуста", font=("Arial", 14))
        self.empty_label.pack(pady=50)

    def start_queue(self):
        self.download_queue.start_processing()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

    def stop_queue(self):
        self.download_queue.stop_processing()
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def clear_completed(self):
        self.download_queue.clear_completed()
        self.refresh_queue()

    def on_concurrent_changed(self, value):
        concurrent = int(value)
        self.concurrent_label.configure(text=str(concurrent))
        self.download_queue.set_max_concurrent(concurrent)

    def refresh_queue(self):
        for widget in self.queue_frame.winfo_children():
            widget.destroy()

        items = self.download_queue.get_all_items()

        if not items:
            self.empty_label = ctk.CTkLabel(self.queue_frame, text="Очередь пуста", font=("Arial", 14))
            self.empty_label.pack(pady=50)
            return

        for item in items:
            self.create_item_widget(item)

    def create_item_widget(self, item):
        item_frame = ctk.CTkFrame(self.queue_frame)
        item_frame.pack(fill="x", padx=5, pady=5)

        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)

        title_label = ctk.CTkLabel(info_frame, text=item['title'], font=("Arial", 12, "bold"), anchor="w")
        title_label.pack(fill="x")

        url_label = ctk.CTkLabel(info_frame, text=item['url'][:80] + "..." if len(item['url']) > 80 else item['url'],
                                 font=("Arial", 10), anchor="w", text_color="gray")
        url_label.pack(fill="x")

        status_color_map = {
            'queued': 'gray',
            'downloading': 'blue',
            'completed': 'green',
            'error': 'red'
        }

        status_text_map = {
            'queued': 'В очереди',
            'downloading': 'Загружается',
            'completed': 'Завершено',
            'error': 'Ошибка'
        }

        status_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        status_frame.pack(fill="x", pady=(5, 0))

        status_text = status_text_map.get(item['status'], item['status'])
        status_label = ctk.CTkLabel(status_frame, text=f"Статус: {status_text}",
                                    font=("Arial", 10), anchor="w",
                                    text_color=status_color_map.get(item['status'], 'white'))
        status_label.pack(side="left")

        if item['status'] == 'downloading':
            progress_text = f" | Прогресс: {item['progress']:.1f}%"
            if item['speed']:
                progress_text += f" | Скорость: {item['speed']}"
            if item['eta']:
                progress_text += f" | Осталось: {item['eta']}"

            progress_label = ctk.CTkLabel(status_frame, text=progress_text, font=("Arial", 10), anchor="w")
            progress_label.pack(side="left", padx=(10, 0))

            progress_bar = ctk.CTkProgressBar(item_frame)
            progress_bar.pack(fill="x", padx=10, pady=(0, 10))
            progress_bar.set(item['progress'] / 100)

        elif item['status'] == 'completed':
            filesize = item.get('filesize', 0)
            if filesize > 0:
                size_mb = filesize / (1024 * 1024)
                size_label = ctk.CTkLabel(status_frame, text=f" | Размер: {size_mb:.1f} MB",
                                         font=("Arial", 10), anchor="w")
                size_label.pack(side="left", padx=(10, 0))

        elif item['status'] == 'error':
            error_label = ctk.CTkLabel(info_frame, text=f"Ошибка: {item.get('error_message', 'Unknown')}",
                                      font=("Arial", 9), anchor="w", text_color="red")
            error_label.pack(fill="x", pady=(5, 0))

        if item['status'] == 'queued':
            remove_btn = ctk.CTkButton(item_frame, text="Удалить", command=lambda: self.remove_item(item['id']),
                                      width=80, height=28)
            remove_btn.pack(side="right", padx=10, pady=(0, 10))

    def remove_item(self, item_id):
        self.download_queue.remove_item(item_id)
        self.refresh_queue()
