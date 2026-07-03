# Pointcloud-Tile

Тайловый сервис для эффективного хранения, обработки и раздачи **облаков точек** (LiDAR) с поддержкой протоколов **TMS** и **WMTS**.

## Возможности

- **Предобработка**: чтение LAS/LAZ/PLY, нормализация координат, фильтрация выбросов
- **Тайлирование**: пространственная нарезка (квадродерево), LoD-пирамида (5 уровней)
- **HTTP API**: TMS и WMTS (GetCapabilities, GetTile, GetFeatureInfo)
- **Кэширование**: Redis с TTL и инвалидацией по слою
- **Хранилище**: локальная ФС или S3-совместимое (MinIO)
- **CLI**: пакетная нарезка и запуск сервера

## Требования

- Python 3.11+
- Redis 7+ (кэш)
- MinIO (опционально, для S3-хранилища)
- PDAL (опционально, для расширенной фильтрации — устанавливается через apt/conda)

## Быстрый старт

### Docker Compose (рекомендуется)

```bash
cp .env.example .env
docker compose up -d --build
```

Сервис доступен на http://localhost:8000

- MinIO Console: http://localhost:9001
- Swagger UI: http://localhost:8000/docs

### Локальная установка

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env
```

### Тайлирование

```bash
pointcloud-tile tile /path/to/cloud.laz --layer my-layer
```

### Запуск сервера

```bash
pointcloud-tile serve --host 0.0.0.0 --port 8000
```

## API

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/tms/{version}/{layer}/{z}/{x}/{y}.{format}` | TMS-тайл |
| GET | `/wmts?REQUEST=GetCapabilities` | WMTS capabilities |
| GET | `/wmts?REQUEST=GetTile&...` | WMTS-тайл |
| GET | `/layers` | Список слоёв |
| GET | `/layers/{name}` | Метаданные слоя |

Подробнее: [docs/protocol-specification.md](docs/protocol-specification.md)

### Пример запроса TMS

```
GET /tms/1.0.0/my-layer/2/1/3.laz?lod=2&height_min=0&height_max=100
```

## Архитектура

```
src/pointcloud_tile/
├── preprocessing/   # Чтение, нормализация, фильтры
├── tiling/          # Квадродерево, LoD, pipeline
├── storage/         # Файловая система / S3
├── cache/           # Redis
├── api/             # FastAPI (TMS, WMTS)
├── models/          # Доменные модели
├── config.py        # Настройки (pydantic-settings)
└── cli.py           # CLI-утилита
```

## Тестирование

```bash
# Unit-тесты
pytest tests/ -m "not integration and not slow"

# Нагрузочное тестирование (Locust)
docker compose --profile loadtest up locust
# UI: http://localhost:8089
```

## Конфигурация

Все параметры задаются через переменные окружения или `.env`. См. [.env.example](.env.example).

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `STORAGE_BACKEND` | `filesystem` | `filesystem` или `s3` |
| `LOD_LEVELS` | `5` | Число уровней LoD (0–4) |
| `REDIS_URL` | `redis://redis:6379/0` | URL Redis |
| `CACHE_TTL_SECONDS` | `3600` | TTL кэша тайлов |

## Нефункциональные требования (целевые)

- Отклик из кэша: ≤ 200 мс при 100 одновременных запросах
- Скорость тайлирования: ≥ 10 млн точек/мин (8 CPU, 32 GB RAM)
- Размер тайла LoD 0: ≤ 5 МБ (сжатый LAZ)
- Горизонтальное масштабирование HTTP-сервера без изменения кода

## Лицензия

MIT
