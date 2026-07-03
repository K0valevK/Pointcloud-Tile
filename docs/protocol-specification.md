# Спецификация расширения TMS/WMTS для трёхмерных тайлов облаков точек

## 1. Обзор

Данный документ описывает расширение стандартных протоколов **TMS** (Tile Map Service) и **WMTS** (Web Map Tile Service) для раздачи трёхмерных тайлов облаков точек.

## 2. TMS

### 2.1. Шаблон URL

```
GET /tms/{version}/{layer}/{z}/{x}/{y}.{format}
```

| Параметр  | Описание                                      |
|-----------|-----------------------------------------------|
| version   | Версия API (например, `1.0.0`)                |
| layer     | Идентификатор слоя                            |
| z, x, y   | Координаты тайла в пространственном индексе   |
| format    | `laz` (сжатый LAS) или `bin` (бинарный поток) |

### 2.2. Query-параметры фильтрации

| Параметр        | Тип    | Описание                          |
|-----------------|--------|-----------------------------------|
| lod             | int    | Уровень детализации (0–4)         |
| intensity_min   | float  | Мин. интенсивность                |
| intensity_max   | float  | Макс. интенсивность               |
| classification  | string | Классы через запятую (LAS class)  |
| height_min      | float  | Мин. высота (Z)                   |
| height_max      | float  | Макс. высота (Z)                  |

### 2.3. MIME-типы

- `application/vnd.laz` — LAZ-тайл
- `application/octet-stream` — бинарный формат Pointcloud-Tile

## 3. WMTS

### 3.1. GetCapabilities

```
GET /wmts?SERVICE=WMTS&REQUEST=GetCapabilities&VERSION=1.0.0
```

XML-ответ содержит блок `VendorSpecificCapabilities/Extension` с атрибутами:

- `type="pointcloud"`
- `LoDLevels` — доступные уровни LoD
- `TileFormats` — поддерживаемые форматы

### 3.2. GetTile

```
GET /wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0
    &LAYER={layer}&STYLE=default&TILEMATRIXSET=EPSG:4326
    &TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&FORMAT={format}&lod={lod}
```

### 3.3. GetFeatureInfo

```
GET /wmts?SERVICE=WMTS&REQUEST=GetFeatureInfo&...
```

Возвращает JSON с точками в области пикселя (i, j) — для интерактивного запроса атрибутов.

## 4. Бинарный формат `bin`

```
[count: uint32 LE][x: float32, y: float32, z: float32] × count
```

## 5. LoD-пирамида

Каждый пространственный тайл (z/x/y) содержит 5 уровней детализации (LoD 0–4):

- **LoD 0** — полное разрешение (≤ 5 МБ сжатый LAZ)
- **LoD 1–4** — прогрессивное прореживание (voxel-grid + сохранение экстремумов)

## 6. Метаданные слоя

```
GET /layers/{layer_name}
```

JSON: `name`, `title`, `bbox`, `crs`, `lod_levels`, `point_count`, `tile_formats`.
