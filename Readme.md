# HSE NoSQL итоговое ДЗ по модулю 3

Курс: Нереляционные базы данных 25-26
Факультет: Инженерия данных
Студент: Петр Бондарев

Реализация итогового задания в Яндекс Облаке:
- шардинг MongoDB
- Python CLI
- нагрузочное тестирование
- итоговый отчёт

## Быстрый старт

1. Установить зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Инфраструктура уже развёрнута в Яндекс Облаке:

- VM: `hse-nosql-app-vm` (`89.169.183.108`, SSH alias: `ya-mongo`)
- MongoDB cluster: `hse-nosql-mongo` (`c9qdjse6diu0afl6ad4p`)
- База: `university`
- Пользователь: `app_user`

3. Подготовить URI подключения к MongoDB (реальные хосты кластера):

```bash
export MONGO_URI="mongodb://app_user:<ПАРОЛЬ_ИЗ_infra/.mongo_password>@rc1a-3ab60mpph4ojgmmm.mdb.yandexcloud.net:27018,rc1b-keosa985gsajqa6a.mdb.yandexcloud.net:27018,rc1d-toeqcdct7hrdf5tl.mdb.yandexcloud.net:27018/university?tls=true&replicaSet=rs0&authSource=university"
```

Примечание: для `mongosh` в Managed MongoDB может понадобиться CA-сертификат Яндекс Облака (`--tls --tlsCAFile`).

4. Инициализировать схему БД и загрузить тестовые данные:

```bash
mongosh "$MONGO_URI" --file db/init_schema.js
python db/seed_data.py --mongo-uri "$MONGO_URI" --students 5000 --courses-per-dept 20
```

5. Запустить CLI:

```bash
python app/cli.py --mongo-uri "$MONGO_URI" find-student --student-id CS-STU-000001
```

6. Запустить нагрузочные тесты:

```bash
export MONGO_URI="$MONGO_URI"
bash tests/load/run_load.sh
python tests/load/plot_results.py
```

Полный отчёт: `report/README.md`.

