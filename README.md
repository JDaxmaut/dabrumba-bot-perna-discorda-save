# Discord papka uplodere BOT SKYNET VAGUE porna vidosa ugabuga child po from kung fu panda

Бот для Discord: следит за папкой на пк, при появлении новой папки внутри создает канал с её именем (категорию выбираешь сам) и заливает туда все файлы.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![discord.py](https://img.shields.io/badge/discord.py-2.x-purple)
![Status](https://img.shields.io/badge/status-working-green)

## Как работает

1. Кладёшь папку с фото/инфой в отслеживаемую папку (`watch_folder`).
2. Бот находит её и в канале логов присылает сообщение с выпадающим списком категорий сервера.
3. Выбираешь категорию (или «без категории») - бот создаёт текстовый канал с именем папки и заливает в него файлы (рекурсивно по всем вложенным папкам).
4. Обработанные папки записываются в `done.json`, чтобы не повторяться после перезапуска.

## Установка

```bash
pip install -r requirements.txt
```

Скопируй `config.example.json` в `config.json` и заполни значения.

## Настройка

| Поле | Описание |
|------|----------|
| `token` | токен бота из [Discord Developer Portal](https://discord.com/developers/applications) |
| `guild_id` | ID сервера (режим разработчика -> ПКМ по серверу -> Копировать ID) |
| `log_channel_id` | ID канала, куда бот шлёт сообщение с выбором категории |
| `watch_folder` | полный путь к отслеживаемой папке, например `C:\\Users\\name\\tracked` |
| `poll_interval_seconds` | как часто проверяется папка (сек) |
| `upload_delay_seconds` | пауза между отправкой файлов (сек) |

Для бота на сервере нужны права `Manage Channels` и `Send Messages`. В Developer Portal у бота включи `SERVER MEMBERS INTENT` не требуется, обычного бота хватает.

## Запуск

```bash
python bot.py
```

## Полезное знать

- файлы больше 25 МБ пропускаются с предупреждением (лимит Discord)
- имя канала приводится к нижнему регистру и без спецсимволов (требование Discord), оригинальное имя хранится в теме канала
- если промпт-сообщение «умерло» (бота перезапускали), брошенные папки заново предложит при следующей проверке
