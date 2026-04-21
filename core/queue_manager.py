from queue import Queue
import threading
import uuid
from typing import Dict, Any, Callable, Optional, List
from core.downloader import YTDLPDownloader


class DownloadItem:
    def __init__(self, url: str, options: Dict[str, Any]):
        self.id = str(uuid.uuid4())
        self.url = url
        self.title = options.get('title', 'Unknown')
        self.status = 'queued'
        self.progress = 0.0
        self.speed = ''
        self.eta = ''
        self.filesize = 0
        self.downloaded_bytes = 0
        self.options = options
        self.error_message = ''

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'url': self.url,
            'title': self.title,
            'status': self.status,
            'progress': self.progress,
            'speed': self.speed,
            'eta': self.eta,
            'filesize': self.filesize,
            'downloaded_bytes': self.downloaded_bytes,
            'error_message': self.error_message,
        }


class DownloadQueue:
    def __init__(self, max_concurrent: int = 3, status_callback: Optional[Callable] = None):
        self.queue = Queue()
        self.active_downloads: List[DownloadItem] = []
        self.completed: List[DownloadItem] = []
        self.all_items: Dict[str, DownloadItem] = {}
        self.max_concurrent = max_concurrent
        self.is_running = False
        self.status_callback = status_callback
        self.lock = threading.Lock()

    def add_to_queue(self, download_item: DownloadItem) -> str:
        """Добавить элемент в очередь"""
        with self.lock:
            self.all_items[download_item.id] = download_item
            self.queue.put(download_item)
            self._notify_status_change()
        return download_item.id

    def start_processing(self):
        """Запустить обработку очереди"""
        if not self.is_running:
            self.is_running = True
            threading.Thread(target=self._process_queue, daemon=True).start()

    def stop_processing(self):
        """Остановить обработку очереди"""
        self.is_running = False

    def _process_queue(self):
        """Обработка очереди в фоновом потоке"""
        while self.is_running:
            with self.lock:
                active_count = len(self.active_downloads)

            if active_count < self.max_concurrent and not self.queue.empty():
                item = self.queue.get()
                self._start_download(item)

            threading.Event().wait(0.5)

    def _start_download(self, item: DownloadItem):
        """Запустить загрузку элемента"""
        with self.lock:
            item.status = 'downloading'
            self.active_downloads.append(item)
            self._notify_status_change()

        def progress_callback(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)

                if total > 0:
                    item.progress = (downloaded / total) * 100
                    item.filesize = total
                    item.downloaded_bytes = downloaded

                item.speed = d.get('_speed_str', '')
                item.eta = d.get('_eta_str', '')
                self._notify_status_change()

            elif d['status'] == 'finished':
                item.progress = 100
                self._notify_status_change()

        def completion_callback(success: bool, error: Optional[str]):
            with self.lock:
                if item in self.active_downloads:
                    self.active_downloads.remove(item)

                if success:
                    item.status = 'completed'
                    item.progress = 100
                else:
                    item.status = 'error'
                    item.error_message = error or 'Unknown error'

                self.completed.append(item)
                self._notify_status_change()

        downloader = YTDLPDownloader(progress_callback=progress_callback)
        downloader.download_async(item.url, item.options, completion_callback)

    def get_all_items(self) -> List[Dict[str, Any]]:
        """Получить все элементы очереди"""
        with self.lock:
            queued = [item.to_dict() for item in list(self.queue.queue)]
            active = [item.to_dict() for item in self.active_downloads]
            completed = [item.to_dict() for item in self.completed]
            return queued + active + completed

    def get_item(self, item_id: str) -> Optional[DownloadItem]:
        """Получить элемент по ID"""
        with self.lock:
            return self.all_items.get(item_id)

    def remove_item(self, item_id: str) -> bool:
        """Удалить элемент из очереди"""
        with self.lock:
            item = self.all_items.get(item_id)
            if item and item.status == 'queued':
                temp_queue = Queue()
                while not self.queue.empty():
                    queued_item = self.queue.get()
                    if queued_item.id != item_id:
                        temp_queue.put(queued_item)
                self.queue = temp_queue
                del self.all_items[item_id]
                self._notify_status_change()
                return True
            return False

    def clear_completed(self):
        """Очистить завершенные загрузки"""
        with self.lock:
            for item in self.completed:
                if item.id in self.all_items:
                    del self.all_items[item.id]
            self.completed.clear()
            self._notify_status_change()

    def set_max_concurrent(self, max_concurrent: int):
        """Установить максимальное количество параллельных загрузок"""
        with self.lock:
            self.max_concurrent = max(1, min(max_concurrent, 10))

    def _notify_status_change(self):
        """Уведомить о изменении статуса"""
        if self.status_callback:
            self.status_callback()
