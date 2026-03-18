# Итоговый отчёт: модуль 3 (NoSQL)

**Курс:** Нереляционные базы данных 25-26
**Факультет:** Инженерия данных
**Студент:** Петр Бондарев

---

## Содержание

1. [Быстрый старт](#1-быстрый-старт)
2. [Проектирование базы данных](#2-проектирование-базы-данных)
3. [Настройка базы данных](#3-настройка-базы-данных)
4. [Шардирование и обоснование](#4-шардирование-и-обоснование)
5. [Python CLI](#5-python-cli)
6. [Нагрузочное тестирование](#6-нагрузочное-тестирование)
7. [Инфраструктура Яндекс Облака](#7-инфраструктура-яндекс-облака)
8. [Структура репозитория](#8-структура-репозитория)

---

## 1. Быстрый старт

### 1.1. Установка зависимостей

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 1.2. Инфраструктура

Инфраструктура развёрнута в Яндекс Облаке:

| Ресурс | Значение |
|--------|----------|
| VM | `hse-nosql-app-vm` (`89.169.183.108`) |
| MongoDB cluster | `hse-nosql-mongo` (`c9qdjse6diu0afl6ad4p`) |
| База данных | `university` |
| Пользователь | `app_user` |

### 1.3. Подключение к MongoDB

Скачать CA-сертификат Яндекс Облака и сформировать URI:

```bash
mkdir -p ~/.mongodb && wget -q "https://storage.yandexcloud.net/cloud-certs/CA.pem" -O ~/.mongodb/root.crt
ENCODED_PASS=$(python3 -c "import urllib.parse; print(urllib.parse.quote(open('infra/.mongo_password').read().strip()))")
export MONGO_URI="mongodb://app_user:${ENCODED_PASS}@rc1a-3ab60mpph4ojgmmm.mdb.yandexcloud.net:27017,rc1b-keosa985gsajqa6a.mdb.yandexcloud.net:27017,rc1d-toeqcdct7hrdf5tl.mdb.yandexcloud.net:27017/university?tls=true&tlsCAFile=$HOME/.mongodb/root.crt&authSource=university"
```

### 1.4. Инициализация схемы и загрузка данных

```bash
mongosh "$MONGO_URI" --file db/init_schema.js
python db/seed_data.py --mongo-uri "$MONGO_URI" --students 5000 --courses-per-dept 20
```

### 1.5. Запуск CLI

```bash
python app/cli.py --mongo-uri "$MONGO_URI" find-student --student-id MATH-STU-000001
```

### 1.6. Запуск нагрузочных тестов

```bash
export MONGO_URI="$MONGO_URI"
bash tests/load/run_load.sh
python tests/load/plot_results.py
```

---

## 2. Проектирование базы данных

### 2.1. Область применения

Модель данных поддерживает:

- регистрацию студентов;
- каталог курсов и преподавателей;
- запись студентов на курсы;
- выставление оценок по семестрам;
- аналитические выборки по кафедре, группе и курсу обучения.

### 2.2. Коллекции

#### `departments` — кафедры

| Поле | Тип | Описание |
|------|-----|----------|
| `departmentId` | string, unique | Идентификатор кафедры |
| `name` | string | Название |
| `faculty` | string | Факультет |

#### `students` — студенты

| Поле | Тип | Описание |
|------|-----|----------|
| `studentId` | string, unique | Идентификатор студента |
| `firstName` | string | Имя |
| `lastName` | string | Фамилия |
| `email` | string, unique | Электронная почта |
| `departmentId` | string | Кафедра |
| `group` | string | Группа |
| `year` | int (1–6) | Курс обучения |
| `enrolledAt` | date | Дата зачисления |
| `status` | string | `active`, `academic_leave`, `graduated`, `expelled` |

#### `instructors` — преподаватели

| Поле | Тип | Описание |
|------|-----|----------|
| `instructorId` | string, unique | Идентификатор преподавателя |
| `firstName` | string | Имя |
| `lastName` | string | Фамилия |
| `departmentId` | string | Кафедра |
| `email` | string, unique | Электронная почта |

#### `courses` — курсы

| Поле | Тип | Описание |
|------|-----|----------|
| `courseId` | string, unique | Идентификатор курса |
| `title` | string | Название |
| `departmentId` | string | Кафедра |
| `credits` | int | Кредиты (зачётные единицы) |
| `semesterOffered` | string | Семестр (напр. `2026-Spring`) |
| `instructorId` | string | Преподаватель |

#### `enrollments` — записи на курсы (шардированная коллекция)

| Поле | Тип | Описание |
|------|-----|----------|
| `enrollmentId` | string, unique | Идентификатор записи |
| `departmentId` | string | Кафедра |
| `studentId` | string | Студент |
| `courseId` | string | Курс |
| `semester` | string | Семестр |
| `enrolledAt` | date | Дата записи |
| `status` | string | `enrolled`, `dropped`, `completed` |

#### `grades` — оценки

| Поле | Тип | Описание |
|------|-----|----------|
| `gradeId` | string, unique | Идентификатор оценки |
| `studentId` | string | Студент |
| `courseId` | string | Курс |
| `semester` | string | Семестр |
| `grade` | string | `A`, `B`, `C`, `D`, `F`, `Pass`, `Fail` |
| `updatedAt` | date | Дата обновления |

### 2.3. Логическая схема связей

```mermaid
flowchart LR
  departments --> students
  departments --> instructors
  departments --> courses
  instructors --> courses
  students --> enrollments
  courses --> enrollments
  students --> grades
  courses --> grades
```

### 2.4. План индексов

| Коллекция | Индекс | Тип |
|-----------|--------|-----|
| `students` | `studentId` | unique |
| `students` | `email` | unique |
| `students` | `{ departmentId: 1, year: 1 }` | compound |
| `courses` | `courseId` | unique |
| `courses` | `{ departmentId: 1, semesterOffered: 1 }` | compound |
| `enrollments` | `enrollmentId` | unique |
| `enrollments` | `{ departmentId: 1, studentId: 1, courseId: 1 }` | compound |
| `enrollments` | `{ semester: 1, departmentId: 1 }` | compound |
| `grades` | `gradeId` | unique |
| `grades` | `{ studentId: 1, semester: 1 }` | compound |
| `grades` | `{ courseId: 1, semester: 1 }` | compound |

### 2.5. Типичные паттерны запросов

1. Поиск профиля студента и его активных записей по `studentId`.
2. Список студентов кафедры на определённом курсе обучения.
3. Все записи на курсы по кафедре и семестру.
4. Расчёт среднего балла (GPA) студента по оценкам.

---

## 3. Настройка базы данных

### 3.1. Инициализация схемы, индексов и шардирования

```bash
mongosh "$MONGO_URI" --file db/init_schema.js
```

Скрипт `db/init_schema.js` создаёт 6 коллекций с JSON Schema-валидаторами и все индексы из плана выше.

### 3.2. Загрузка синтетических данных

```bash
python db/seed_data.py \
  --mongo-uri "$MONGO_URI" \
  --students 5000 \
  --courses-per-dept 20
```

Результат загрузки:

| Коллекция | Количество записей |
|-----------|--------------------|
| departments | 6 |
| instructors | 60 |
| courses | 120 |
| students | 5 000 |
| enrollments | 29 939 |
| grades | 25 475 |

Общий объём: ~60 600 документов.

---

## 4. Шардирование и обоснование

### 4.1. Шардируемая коллекция

Основная рабочая коллекция — `enrollments`. Это самая крупная и наиболее активно используемая коллекция (чтение + запись).

### 4.2. Ключ шардирования

```js
sh.shardCollection("university.enrollments", { departmentId: 1, studentId: 1 })
```

### 4.3. Обоснование выбора ключа

| Критерий | Оценка |
|----------|--------|
| **Кардинальность** | Высокая — составной ключ (кафедра + студент) обеспечивает равномерное распределение |
| **Локальность запросов** | Большинство запросов фильтруют по `departmentId` и/или `studentId` — попадание в один шард |
| **Отсутствие hot-spot** | Составной ключ избегает концентрации записей на одном шарде (в отличие от одно-польного ключа) |
| **Масштабируемость** | При росте данных добавление шардов приводит к линейному масштабированию |

### 4.4. Перспективы

Коллекция `students` остаётся нешардированной при текущем объёме. При значительном росте можно шардировать по `{ departmentId: 1, studentId: 1 }` для колокации с паттернами доступа к `enrollments`.

---

## 5. Python CLI

CLI реализован в `app/cli.py` на основе `pymongo` и `argparse`.

### 5.1. Поддерживаемые команды

| Команда | Описание |
|---------|----------|
| `create-student` | Создание нового студента |
| `find-student` | Поиск студента по ID |
| `enroll` | Запись студента на курс |
| `add-grade` | Выставление оценки |
| `student-report` | Отчёт по успеваемости студента |

### 5.2. Примеры использования

Создание студента:

```bash
python app/cli.py --mongo-uri "$MONGO_URI" \
  create-student \
  --student-id CS-STU-900001 \
  --first-name Иван \
  --last-name Петров \
  --email cs-stu-900001@students.university.edu \
  --department-id CS \
  --group CS-01 \
  --year 2
```

Поиск студента:

```bash
python app/cli.py --mongo-uri "$MONGO_URI" \
  find-student --student-id MATH-STU-000001
```

Отчёт по успеваемости:

```bash
python app/cli.py --mongo-uri "$MONGO_URI" \
  student-report --student-id MATH-STU-000001
```

### 5.3. Замер времени

Каждая операция CLI замеряет время выполнения запроса к MongoDB и выводит его в консоль (например, `find-student completed in 50.39 ms`).

---

## 6. Нагрузочное тестирование

### 6.1. Инструмент

**Locust** — Python-фреймворк нагрузочного тестирования. Файл сценария: `tests/load/locustfile.py`.

### 6.2. Сценарии нагрузки

Тестируется смешанная нагрузка (mixed) с весовыми коэффициентами задач:

| Операция | Тип | Вес | Описание |
|----------|-----|-----|----------|
| `find_student` | чтение | 6 | Поиск профиля студента по случайному `studentId` |
| `find_enrollments` | чтение | 4 | Список записей по кафедре и семестру (LIMIT 100) |
| `insert_enrollment` | запись | 2 | Вставка новой записи на курс |

Соотношение чтение/запись: **83% / 17%**.

### 6.3. Параметры запуска

| Параметр | Baseline | Scaled |
|----------|----------|--------|
| Количество пользователей | 20 | 80 |
| Скорость запуска (users/sec) | 5 | 10 |
| Длительность | 2 мин | 2 мин |

### 6.4. Результаты: Baseline (20 пользователей)

| Операция | Запросов | Ошибок | Avg (мс) | Median (мс) | p95 (мс) | Max (мс) | RPS |
|----------|----------|--------|----------|-------------|----------|----------|-----|
| `find_student` | 2 061 | 0 | 12.2 | 10 | 16 | 259 | 17.3 |
| `find_enrollments` | 1 469 | 0 | 12.8 | 11 | 17 | 237 | 12.3 |
| `insert_enrollment` | 693 | 0 | 16.5 | 13 | 27 | 298 | 5.8 |
| **Итого** | **4 223** | **0** | **13.1** | **11** | **19** | **298** | **35.4** |

### 6.5. Результаты: Scaled (80 пользователей)

| Операция | Запросов | Ошибок | Avg (мс) | Median (мс) | p95 (мс) | Max (мс) | RPS |
|----------|----------|--------|----------|-------------|----------|----------|-----|
| `find_student` | 8 156 | 0 | 13.9 | 10 | 17 | 491 | 68.4 |
| `find_enrollments` | 5 462 | 0 | 14.8 | 11 | 18 | 494 | 45.8 |
| `insert_enrollment` | 2 734 | 1 | 18.8 | 15 | 30 | 485 | 22.9 |
| **Итого** | **16 352** | **1 (0.006%)** | **15.0** | **11** | **21** | **494** | **137.1** |

### 6.6. Сравнительная таблица

| Метрика | Baseline (20) | Scaled (80) | Изменение |
|---------|---------------|-------------|-----------|
| Throughput (RPS) | 35.4 | 137.1 | **×3.9** |
| Avg latency (мс) | 13.1 | 15.0 | +14% |
| p95 latency (мс) | 19 | 21 | +11% |
| Error rate | 0% | 0.006% | — |

### 6.7. Выводы

1. **Пропускная способность** масштабируется почти линейно: при увеличении пользователей в 4 раза, RPS вырос в 3.9 раза.
2. **Задержки** остаются стабильными: средняя задержка выросла всего на 14% (с 13 до 15 мс), p95 — на 11%.
3. **Ошибок** практически нет: 1 из 16 352 запросов (коллизия случайных ID при вставке).
4. **Операции записи** ожидаемо медленнее чтения (18.8 мс vs 13.9 мс), но разница невелика.
5. Кластер уверенно справляется с нагрузкой в 137 RPS при p95 < 30 мс.

### 6.8. График

![Результаты нагрузочного тестирования](../tests/load/results/summary.png)

### 6.9. Артефакты

- `tests/load/results/baseline_stats.csv` — статистика baseline-теста
- `tests/load/results/scaled_stats.csv` — статистика scaled-теста
- `tests/load/results/summary.png` — сводный график

---

## 7. Инфраструктура Яндекс Облака

Terraform-конфигурация в `infra/terraform/` разворачивает:

| Ресурс | Описание |
|--------|----------|
| `yandex_vpc_network` | VPC-сеть |
| `yandex_vpc_subnet` × 2 | Подсети в зонах `ru-central1-a` и `ru-central1-b` |
| `yandex_vpc_security_group` | Правила доступа (MongoDB порт 27017, SSH порт 22) |
| `yandex_mdb_mongodb_cluster` | Шардированный MongoDB-кластер (2 шарда MONGOD + MONGOINFRA) |
| `yandex_compute_instance` | VM для CLI и нагрузочных тестов |

Кластер MongoDB:
- Версия: 6.0
- Тип: шардированный (`sharded = true`)
- Ресурсы: `s2.micro`, 20 ГБ SSD на каждый хост
- Шарды: `rs-shard-a` (зона a), `rs-shard-b` (зона b)
- MONGOINFRA: зона a (mongos + config server)

---

## 8. Структура репозитория

```
HSE-NoSQL/
├── infra/
│   ├── terraform/          # IaC для Яндекс Облака
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── versions.tf
│   └── .mongo_password     # Пароль MongoDB
├── db/
│   ├── DESIGN.md           # Проектирование схемы БД
│   ├── init_schema.js      # Инициализация схемы и индексов
│   └── seed_data.py        # Генерация синтетических данных
├── app/
│   └── cli.py              # Python CLI-интерфейс
├── tests/
│   └── load/
│       ├── locustfile.py   # Сценарии нагрузочного тестирования
│       ├── run_load.sh     # Скрипт запуска тестов
│       ├── plot_results.py # Построение графиков
│       └── results/        # Результаты (CSV + PNG)
├── report/
│   └── README.md           # Данный отчёт
├── requirements.txt
└── Readme.md               # Быстрый старт
```
