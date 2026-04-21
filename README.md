# yt-dlp GUI

Графический интерфейс для утилиты [yt-dlp](https://github.com/yt-dlp/yt-dlp) с поддержкой расширенных настроек, очереди загрузок и профилей.

Репозиторий: [github.com/fox67rus/yt-dpl-gui](https://github.com/fox67rus/yt-dpl-gui)

## Быстрый старт

```bash
git clone https://github.com/fox67rus/yt-dpl-gui.git
cd yt-dpl-gui
python -m venv venv
```

Активируйте виртуальное окружение и установите зависимости:

**Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`  
**Linux/macOS:** `source venv/bin/activate`

```bash
pip install -r requirements.txt
pip install -U "yt-dlp[default]"
python main.py
```

Для стабильной работы с YouTube установите [Deno](https://deno.land/) (см. раздел «Установка» ниже).

## Возможности

- 🎨 Современный интерфейс на базе CustomTkinter
- 📥 Загрузка видео с различных платформ
- 👁️ Предпросмотр информации о видео перед загрузкой
- 🔄 Очередь загрузок с параллельной обработкой
- 🍪 Поддержка cookies Firefox для загрузки приватного контента
- ⚙️ Расширенные настройки (субтитры, качество, метаданные)
- 📋 Профили настроек для быстрого переключения
- 🌙 Темная и светлая темы

## Установка

### Предварительные требования

Для корректной работы с YouTube и другими платформами необходимо установить дополнительные компоненты:

#### 1. Установка Deno (JavaScript runtime)

yt-dlp требует JavaScript runtime для решения защиты YouTube.

**Windows (PowerShell):**
```powershell
irm https://deno.land/install.ps1 | iex
```

**Linux/macOS:**
```bash
curl -fsSL https://deno.land/install.sh | sh
```

После установки **перезапустите терминал** и проверьте:
```bash
deno --version
```

#### 2. Установка Python зависимостей

Склонируйте [репозиторий](https://github.com/fox67rus/yt-dpl-gui) (рекомендуется виртуальное окружение `python -m venv venv`), затем:

```bash
pip install -r requirements.txt
```

#### 3. Установка yt-dlp с поддержкой EJS

Для работы с YouTube необходимо установить yt-dlp с дополнительными компонентами:

```bash
pip install -U "yt-dlp[default]"
```

Это установит пакет `yt-dlp-ejs`, который работает вместе с Deno для обхода защиты YouTube.

### Возможные проблемы

**Ошибка "n challenge solving failed":**
- Убедитесь, что Deno установлен и доступен в PATH
- Перезапустите терминал после установки Deno
- Установите `yt-dlp[default]` как указано выше

**Ошибка "Only images are available":**
- Это означает, что JavaScript runtime не найден
- Следуйте инструкциям по установке Deno выше

Подробнее: [yt-dlp EJS Wiki](https://github.com/yt-dlp/yt-dlp/wiki/EJS)

## Использование

Запустите приложение:
```bash
python main.py
```

### Основные функции

#### Вкладка "Загрузка"
- Вставьте URL видео
- Нажмите "Предпросмотр" для просмотра информации
- Выберите формат и качество
- Настройте дополнительные параметры
- Нажмите "Загрузить сейчас" или "Добавить в очередь"

#### Вкладка "Очередь"
- Просмотр всех загрузок
- Управление очередью (запуск/остановка)
- Настройка количества параллельных загрузок
- Удаление элементов из очереди

#### Вкладка "Настройки"
- Настройка папки загрузок по умолчанию
- Изменение темы интерфейса
- Настройка параметров загрузки
- Проверка статуса Firefox cookies

#### Вкладка "Профили"
- Создание профилей с разными настройками
- Редактирование существующих профилей
- Дублирование и удаление профилей

## Требования

- Python 3.7+ (рекомендуется 3.10+)
- зависимости из `requirements.txt` (включая `customtkinter`, `Pillow`, `requests`, `yt-dlp`)

## Структура проекта

```
yt-dlp-gui/
├── main.py                 # Точка входа
├── requirements.txt        # Зависимости
├── config.json            # Конфигурация
├── gui/                   # GUI компоненты
│   ├── main_window.py
│   ├── download_tab.py
│   ├── queue_tab.py
│   ├── settings_tab.py
│   └── profiles_tab.py
├── core/                  # Основная логика
│   ├── downloader.py
│   ├── queue_manager.py
│   ├── config_manager.py
│   └── firefox_cookies.py
└── utils/                 # Вспомогательные функции
    └── helpers.py
```

## Лицензия

[MIT](LICENSE)

