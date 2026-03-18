from __future__ import annotations

import os
import random

from locust import User, between, task
from pymongo import MongoClient


DEPTS = ["CS", "MATH", "PHYS", "ECON", "LING", "BIO"]
SEMESTERS = ["2025-Fall", "2026-Spring"]


class MongoUser(User):
    wait_time = between(0.1, 1.0)

    def on_start(self):
        mongo_uri = os.getenv("MONGO_URI")
        db_name = os.getenv("DB_NAME", "university")
        if not mongo_uri:
            raise RuntimeError("MONGO_URI must be set")
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]

    def _random_student_id(self):
        dept = random.choice(DEPTS)
        seq = random.randint(1, 5000)
        return f"{dept}-STU-{seq:06d}"

    @task(6)
    def read_student_profile(self):
        self.db.students.find_one({"studentId": self._random_student_id()}, {"_id": 0})

    @task(4)
    def read_department_enrollments(self):
        dept = random.choice(DEPTS)
        semester = random.choice(SEMESTERS)
        list(
            self.db.enrollments.find(
                {"departmentId": dept, "semester": semester},
                {"_id": 0, "studentId": 1, "courseId": 1},
            ).limit(100)
        )

    @task(2)
    def write_enrollment(self):
        dept = random.choice(DEPTS)
        student_id = self._random_student_id()
        seq = random.randint(10000000, 99999999)
        self.db.enrollments.insert_one(
            {
                "enrollmentId": f"ENR-LT-{seq}",
                "departmentId": dept,
                "studentId": student_id,
                "courseId": f"{dept}-{random.randint(1, 20):03d}",
                "semester": random.choice(SEMESTERS),
                "status": "enrolled",
            }
        )

