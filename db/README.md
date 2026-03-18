# Database Setup

## 1) Initialize schema, indexes, and sharding

```bash
mongosh "mongodb://app_user:YOUR_PASSWORD@MONGOS_HOST:27017/admin?replicaSet=rs01" --file db/init_schema.js
```

If your connection string is from Managed MongoDB, use that full URI directly.

## 2) Seed synthetic data

```bash
python db/seed_data.py \
  --mongo-uri "mongodb://app_user:YOUR_PASSWORD@MONGOS_HOST:27017/university" \
  --students 5000 \
  --courses-per-dept 20
```

## 3) Check sharding distribution

```bash
mongosh "mongodb://app_user:YOUR_PASSWORD@MONGOS_HOST:27017/admin" --file db/check_sharding.js
```

