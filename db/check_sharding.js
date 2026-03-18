// mongosh script: inspect sharding distribution
// Usage:
// mongosh "mongodb://user:pass@mongos-host:27017/admin" --file db/check_sharding.js

const dbName = "university";
const ns = `${dbName}.enrollments`;
const cfg = db.getSiblingDB("config");

print("=== Sharding status ===");
sh.status();

print("\n=== Chunk distribution by shard for enrollments ===");
const chunks = cfg.chunks.aggregate([
  { $match: { ns } },
  { $group: { _id: "$shard", chunks: { $sum: 1 } } },
  { $sort: { chunks: -1 } },
]).toArray();
printjson(chunks);

print("\n=== Data distribution by department ===");
const perDepartment = db.getSiblingDB(dbName).enrollments.aggregate([
  { $group: { _id: "$departmentId", count: { $sum: 1 } } },
  { $sort: { count: -1 } },
]).toArray();
printjson(perDepartment);

