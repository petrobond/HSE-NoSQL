# Итоговый отчёт: модуль 3 (NoSQL)

## 1. Краткое описание схемы БД

Проект реализован на MongoDB с коллекциями:
- `departments`
- `students`
- `instructors`
- `courses`
- `enrollments`
- `grades`

Подробная схема и обоснование решений: `db/DESIGN.md`.

## 2. Реализация шардинга и обоснование

Шардируется основная рабочая коллекция `enrollments`:

```js
sh.shardCollection("university.enrollments", { departmentId: 1, studentId: 1 })
```

Обоснование:
- высокая кардинальность за счёт составного ключа;
- хорошая локальность университетских запросов по факультету/студенту;
- снижение риска hot-spot по сравнению с одно-польным ключом.

Файл инициализации: `db/init_schema.js`.
Проверка распределения чанков: `db/check_sharding.js`.

## 3. Нагрузочное тестирование

Инструмент: `locust`.

Сценарии:
- read-heavy
- mixed
- write-heavy (через изменение веса write-task)

Команды запуска:

```bash
export MONGO_URI="mongodb://app_user:pass@host:27017/university"
bash tests/load/run_load.sh
python tests/load/plot_results.py
```

Целевые метрики:
- Throughput (`Requests/s`)
- Latency (`p95`, при необходимости `p99`)
- Error rate

Артефакты:
- `tests/load/results/baseline_stats.csv`
- `tests/load/results/scaled_stats.csv`
- `tests/load/results/summary.png`

## 4. Python-интерфейс

CLI реализован в `app/cli.py` (на `pymongo`) и покрывает:
- создание студента;
- поиск студента;
- запись на курс;
- внесение оценки;
- отчёт по успеваемости.

## 5. Инфраструктура Яндекс Облака

Terraform-конфигурация в `infra/terraform/` разворачивает:
- VPC + 2 subnet в разных зонах;
- security group;
- Managed MongoDB sharded cluster;
- отдельную VM для CLI и нагрузочных тестов.

## 6. Структура репозитория

- `infra/terraform/` — IaC для YC
- `db/` — схема, шардирование, сидирование, проверка
- `app/` — Python CLI
- `tests/load/` — нагрузка и визуализация
- `report/README.md` — данный отчёт

## 7. Чек-лист перед сдачей

- [ ] Выполнить `terraform apply` в `infra/terraform`.
- [ ] Применить `db/init_schema.js` на кластере.
- [ ] Засидировать данные `db/seed_data.py`.
- [ ] Провести нагрузочный тест и приложить график.
- [ ] Добавить ссылку на репозиторий в LMS с открытым доступом.

