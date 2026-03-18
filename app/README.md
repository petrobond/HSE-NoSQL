# Python CLI

## Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Examples

```bash
python app/cli.py --mongo-uri "mongodb://app_user:pass@host:27017/university" \
  create-student \
  --student-id CS-STU-000001 \
  --first-name Ivan \
  --last-name Petrov \
  --email cs-stu-000001@students.university.edu \
  --department-id CS \
  --group CS-01 \
  --year 2
```

```bash
python app/cli.py --mongo-uri "mongodb://app_user:pass@host:27017/university" \
  student-report \
  --student-id CS-STU-000001
```

