# Кейс-микрофон: раскладки по цветам

Принтер с одной нитью печатает кейс в несколько заходов: одна печать — один цвет. Детали одного цвета стоят на одном столе, между печатями меняется нить. Порядок печатей в наборе любой.

Каждая раскладка лежит здесь один раз и подходит всем наборам с таким сочетанием деталей. Цвета в файлах нет: его даёт нить, которой печатаете. Номера наборов те же, что на картинках цветов в [README модели](../../README.md#виды). Все детали одним цветом, например для пробной сборки, — в файле [`../aksdom-m31-reporter-mic-case-v1.3mf`](../aksdom-m31-reporter-mic-case-v1.3mf).

Настройки печати — в [README модели](../../README.md#печать). Кайма у головы и ручки уже в модели, в слайсере её надо выключить, поддержки тоже.

Файлы и таблица сделаны скриптом `v1/src/mic_case.py --plates`, надпись в них — пример. Своя надпись: `--top слово --bottom слово --out папка`. От надписи зависят и слова, и выемки в боксе, поэтому пересобирается всё.

## Файлы

| Файл | Что на столе | Габариты, мм (Ш × Г × В) | В скольких наборах |
|---|---|---|---|
| [`aksdom-m31-reporter-mic-case-v1-box.3mf`](aksdom-m31-reporter-mic-case-v1-box.3mf) | бокс | 44 × 44 × 50 | 46 |
| [`aksdom-m31-reporter-mic-case-v1-words.3mf`](aksdom-m31-reporter-mic-case-v1-words.3mf) | надпись | 42 × 23 × 3 | 25 |
| [`aksdom-m31-reporter-mic-case-v1-head-handle.3mf`](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) | голова, ручка | 104 × 55 × 75 | 22 |
| [`aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf`](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) | голова, ручка, надпись | 81 × 104 × 75 | 19 |
| [`aksdom-m31-reporter-mic-case-v1-handle.3mf`](aksdom-m31-reporter-mic-case-v1-handle.3mf) | ручка | 44 × 44 × 75 | 5 |
| [`aksdom-m31-reporter-mic-case-v1-head-words.3mf`](aksdom-m31-reporter-mic-case-v1-head-words.3mf) | голова, надпись | 81 × 55 × 53 | 3 |
| [`aksdom-m31-reporter-mic-case-v1-head.3mf`](aksdom-m31-reporter-mic-case-v1-head.3mf) | голова | 55 × 55 × 53 | 2 |
| [`aksdom-m31-reporter-mic-case-v1-head-box.3mf`](aksdom-m31-reporter-mic-case-v1-head-box.3mf) | голова, бокс | 103 × 55 × 53 | 1 |
| [`aksdom-m31-reporter-mic-case-v1-head-box-handle.3mf`](aksdom-m31-reporter-mic-case-v1-head-box-handle.3mf) | голова, бокс, ручка | 92 × 104 × 75 | 1 |
| [`aksdom-m31-reporter-mic-case-v1-handle-words.3mf`](aksdom-m31-reporter-mic-case-v1-handle-words.3mf) | ручка, надпись | 70 × 50 × 75 | 1 |

## Наборы

Цвета названы как в [FILAMENTS.md](../../../../FILAMENTS.md).

| № | Голова | Бокс | Ручка | Надпись | Печати |
|---|---|---|---|---|---|
| 1 | чёрный | белый | чёрный | красный | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — чёрный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — белый<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — красный |
| 2 | чёрный | белый | чёрный | синий | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — чёрный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — белый<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — синий |
| 3 | белый | белый | жёлтый шёлковый | жёлтый шёлковый | 1. [голова, бокс](aksdom-m31-reporter-mic-case-v1-head-box.3mf) — белый<br>2. [ручка, надпись](aksdom-m31-reporter-mic-case-v1-handle-words.3mf) — жёлтый шёлковый |
| 4 | сине-зелёный шёлковый | белый | сине-зелёный шёлковый | сине-зелёный шёлковый | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — сине-зелёный шёлковый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — белый |
| 5 | красный | белый | красный | красный | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — красный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — белый |
| 6 | синий | белый | синий | синий | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — синий<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — белый |
| 7 | чёрный | чёрный | чёрный | жёлтый шёлковый | 1. [голова, бокс, ручка](aksdom-m31-reporter-mic-case-v1-head-box-handle.3mf) — чёрный<br>2. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — жёлтый шёлковый |
| 8 | жёлтый шёлковый | чёрный | жёлтый шёлковый | жёлтый шёлковый | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — жёлтый шёлковый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — чёрный |
| 9 | белый | чёрный | белый | белый | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — белый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — чёрный |
| 10 | красный | чёрный | красный | красный | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — красный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — чёрный |
| 11 | сине-зелёный шёлковый | чёрный | сине-зелёный шёлковый | сине-зелёный шёлковый | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — сине-зелёный шёлковый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — чёрный |
| 12 | синий | чёрный | синий | белый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — синий<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — чёрный<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — белый |
| 13 | чёрный | красный | чёрный | белый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — чёрный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — красный<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — белый |
| 14 | чёрный | красный | чёрный | жёлтый шёлковый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — чёрный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — красный<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — жёлтый шёлковый |
| 15 | белый | красный | белый | белый | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — белый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — красный |
| 16 | белый | красный | чёрный | белый | 1. [голова, надпись](aksdom-m31-reporter-mic-case-v1-head-words.3mf) — белый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — красный<br>3. [ручка](aksdom-m31-reporter-mic-case-v1-handle.3mf) — чёрный |
| 17 | жёлтый шёлковый | красный | чёрный | жёлтый шёлковый | 1. [голова, надпись](aksdom-m31-reporter-mic-case-v1-head-words.3mf) — жёлтый шёлковый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — красный<br>3. [ручка](aksdom-m31-reporter-mic-case-v1-handle.3mf) — чёрный |
| 18 | синий | красный | синий | белый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — синий<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — красный<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — белый |
| 19 | белый | синий | белый | белый | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — белый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — синий |
| 20 | белый | синий | белый | жёлтый шёлковый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — белый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — синий<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — жёлтый шёлковый |
| 21 | чёрный | синий | чёрный | белый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — чёрный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — синий<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — белый |
| 22 | жёлтый шёлковый | синий | жёлтый шёлковый | жёлтый шёлковый | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — жёлтый шёлковый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — синий |
| 23 | красный | синий | красный | белый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — красный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — синий<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — белый |
| 24 | сине-зелёный шёлковый | синий | сине-зелёный шёлковый | белый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — сине-зелёный шёлковый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — синий<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — белый |
| 25 | чёрный | жёлтый шёлковый | чёрный | чёрный | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — чёрный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — жёлтый шёлковый |
| 26 | белый | жёлтый шёлковый | белый | чёрный | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — белый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — жёлтый шёлковый<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — чёрный |
| 27 | синий | жёлтый шёлковый | синий | синий | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — синий<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — жёлтый шёлковый |
| 28 | красный | жёлтый шёлковый | красный | красный | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — красный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — жёлтый шёлковый |
| 29 | чёрный | жёлтый шёлковый | чёрный | красный | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — чёрный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — жёлтый шёлковый<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — красный |
| 30 | сине-зелёный шёлковый | жёлтый шёлковый | сине-зелёный шёлковый | сине-зелёный шёлковый | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — сине-зелёный шёлковый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — жёлтый шёлковый |
| 31 | чёрный | сине-зелёный шёлковый | чёрный | белый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — чёрный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — сине-зелёный шёлковый<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — белый |
| 32 | белый | сине-зелёный шёлковый | белый | белый | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — белый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — сине-зелёный шёлковый |
| 33 | жёлтый шёлковый | сине-зелёный шёлковый | жёлтый шёлковый | жёлтый шёлковый | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — жёлтый шёлковый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — сине-зелёный шёлковый |
| 34 | чёрный | сине-зелёный шёлковый | чёрный | жёлтый шёлковый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — чёрный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — сине-зелёный шёлковый<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — жёлтый шёлковый |
| 35 | белый | сине-зелёный шёлковый | чёрный | белый | 1. [голова, надпись](aksdom-m31-reporter-mic-case-v1-head-words.3mf) — белый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — сине-зелёный шёлковый<br>3. [ручка](aksdom-m31-reporter-mic-case-v1-handle.3mf) — чёрный |
| 36 | синий | сине-зелёный шёлковый | синий | белый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — синий<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — сине-зелёный шёлковый<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — белый |
| 37 | белый | многоцветный пастельный | белый | чёрный | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — белый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — многоцветный пастельный<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — чёрный |
| 38 | белый | многоцветный пастельный | белый | синий | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — белый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — многоцветный пастельный<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — синий |
| 39 | чёрный | многоцветный пастельный | чёрный | чёрный | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — чёрный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — многоцветный пастельный |
| 40 | чёрный | многоцветный пастельный | чёрный | белый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — чёрный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — многоцветный пастельный<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — белый |
| 41 | красный | многоцветный пастельный | красный | красный | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — красный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — многоцветный пастельный |
| 42 | сине-зелёный шёлковый | многоцветный пастельный | сине-зелёный шёлковый | сине-зелёный шёлковый | 1. [голова, ручка, надпись](aksdom-m31-reporter-mic-case-v1-head-handle-words.3mf) — сине-зелёный шёлковый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — многоцветный пастельный |
| 43 | многоцветный пастельный | белый | многоцветный пастельный | чёрный | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — многоцветный пастельный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — белый<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — чёрный |
| 44 | многоцветный пастельный | чёрный | многоцветный пастельный | белый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — многоцветный пастельный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — чёрный<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — белый |
| 45 | многоцветный пастельный | синий | многоцветный пастельный | белый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — многоцветный пастельный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — синий<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — белый |
| 46 | многоцветный пастельный | красный | многоцветный пастельный | белый | 1. [голова, ручка](aksdom-m31-reporter-mic-case-v1-head-handle.3mf) — многоцветный пастельный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — красный<br>3. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — белый |
| 47 | красный | жёлтый шёлковый | синий | чёрный | 1. [голова](aksdom-m31-reporter-mic-case-v1-head.3mf) — красный<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — жёлтый шёлковый<br>3. [ручка](aksdom-m31-reporter-mic-case-v1-handle.3mf) — синий<br>4. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — чёрный |
| 48 | сине-зелёный шёлковый | красный | жёлтый шёлковый | белый | 1. [голова](aksdom-m31-reporter-mic-case-v1-head.3mf) — сине-зелёный шёлковый<br>2. [бокс](aksdom-m31-reporter-mic-case-v1-box.3mf) — красный<br>3. [ручка](aksdom-m31-reporter-mic-case-v1-handle.3mf) — жёлтый шёлковый<br>4. [надпись](aksdom-m31-reporter-mic-case-v1-words.3mf) — белый |

## Лицензия

Как у модели: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.ru), автор — iruch.
