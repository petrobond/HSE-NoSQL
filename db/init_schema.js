// mongosh script: initialize schema, indexes and sharding
// Usage:
// mongosh "mongodb://user:pass@host:27017/admin" --file db/init_schema.js

const dbName = "university";
const database = db.getSiblingDB(dbName);

const createCollectionWithValidator = (name, validator) => {
  const exists = database.getCollectionNames().includes(name);
  if (!exists) {
    database.createCollection(name, { validator });
    print(`  Created collection: ${name}`);
  } else {
    print(`  Collection already exists: ${name}, skipping`);
  }
};

createCollectionWithValidator("departments", {
  $jsonSchema: {
    bsonType: "object",
    required: ["departmentId", "name", "faculty"],
    properties: {
      departmentId: { bsonType: "string" },
      name: { bsonType: "string" },
      faculty: { bsonType: "string" },
    },
  },
});

createCollectionWithValidator("students", {
  $jsonSchema: {
    bsonType: "object",
    required: ["studentId", "firstName", "lastName", "email", "departmentId", "year", "status"],
    properties: {
      studentId: { bsonType: "string" },
      firstName: { bsonType: "string" },
      lastName: { bsonType: "string" },
      email: { bsonType: "string" },
      departmentId: { bsonType: "string" },
      group: { bsonType: "string" },
      year: { bsonType: "int", minimum: 1, maximum: 6 },
      enrolledAt: { bsonType: "date" },
      status: { enum: ["active", "academic_leave", "graduated", "expelled"] },
    },
  },
});

createCollectionWithValidator("instructors", {
  $jsonSchema: {
    bsonType: "object",
    required: ["instructorId", "firstName", "lastName", "departmentId", "email"],
    properties: {
      instructorId: { bsonType: "string" },
      firstName: { bsonType: "string" },
      lastName: { bsonType: "string" },
      departmentId: { bsonType: "string" },
      email: { bsonType: "string" },
    },
  },
});

createCollectionWithValidator("courses", {
  $jsonSchema: {
    bsonType: "object",
    required: ["courseId", "title", "departmentId", "credits", "semesterOffered", "instructorId"],
    properties: {
      courseId: { bsonType: "string" },
      title: { bsonType: "string" },
      departmentId: { bsonType: "string" },
      credits: { bsonType: "int", minimum: 1, maximum: 8 },
      semesterOffered: { bsonType: "string" },
      instructorId: { bsonType: "string" },
    },
  },
});

createCollectionWithValidator("enrollments", {
  $jsonSchema: {
    bsonType: "object",
    required: ["enrollmentId", "departmentId", "studentId", "courseId", "semester", "status"],
    properties: {
      enrollmentId: { bsonType: "string" },
      departmentId: { bsonType: "string" },
      studentId: { bsonType: "string" },
      courseId: { bsonType: "string" },
      semester: { bsonType: "string" },
      enrolledAt: { bsonType: "date" },
      status: { enum: ["enrolled", "dropped", "completed"] },
    },
  },
});

createCollectionWithValidator("grades", {
  $jsonSchema: {
    bsonType: "object",
    required: ["gradeId", "studentId", "courseId", "semester", "grade"],
    properties: {
      gradeId: { bsonType: "string" },
      studentId: { bsonType: "string" },
      courseId: { bsonType: "string" },
      semester: { bsonType: "string" },
      grade: { enum: ["A", "B", "C", "D", "F", "Pass", "Fail"] },
      updatedAt: { bsonType: "date" },
    },
  },
});

database.departments.createIndex({ departmentId: 1 }, { unique: true });
database.students.createIndex({ studentId: 1 }, { unique: true });
database.students.createIndex({ email: 1 }, { unique: true });
database.students.createIndex({ departmentId: 1, year: 1 });
database.instructors.createIndex({ instructorId: 1 }, { unique: true });
database.instructors.createIndex({ email: 1 }, { unique: true });
database.courses.createIndex({ courseId: 1 }, { unique: true });
database.courses.createIndex({ departmentId: 1, semesterOffered: 1 });
database.enrollments.createIndex({ enrollmentId: 1 }, { unique: true });
database.enrollments.createIndex({ departmentId: 1, studentId: 1, courseId: 1 });
database.enrollments.createIndex({ semester: 1, departmentId: 1 });
database.grades.createIndex({ gradeId: 1 }, { unique: true });
database.grades.createIndex({ studentId: 1, semester: 1 });
database.grades.createIndex({ courseId: 1, semester: 1 });

// Sharding is managed by Yandex Managed MongoDB — enable via cloud console/API
// sh.enableSharding(dbName);
// sh.shardCollection(`${dbName}.enrollments`, { departmentId: 1, studentId: 1 });

print("Schema initialization complete.");

