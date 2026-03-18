#!/usr/bin/env python3
"""Seed synthetic university data into MongoDB."""

from __future__ import annotations

import argparse
import random
from datetime import datetime, timezone

from faker import Faker
from pymongo import MongoClient


GRADE_CHOICES = ["A", "B", "C", "D", "F"]
DEPT_IDS = ["CS", "MATH", "PHYS", "ECON", "LING", "BIO"]
SEMESTERS = ["2025-Fall", "2026-Spring"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed MongoDB with university dataset.")
    parser.add_argument("--mongo-uri", required=True, help="MongoDB connection URI")
    parser.add_argument("--db-name", default="university", help="Database name")
    parser.add_argument("--students", type=int, default=5000, help="Number of students")
    parser.add_argument("--courses-per-dept", type=int, default=20, help="Courses per department")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    return parser.parse_args()


def reset_collections(database) -> None:
    for name in ["departments", "students", "instructors", "courses", "enrollments", "grades"]:
        database[name].delete_many({})


def seed_departments(database) -> list[dict]:
    departments = [
        {"departmentId": dept, "name": f"{dept} Department", "faculty": "Faculty of Sciences"}
        for dept in DEPT_IDS
    ]
    database.departments.insert_many(departments)
    return departments


def seed_instructors(database, fake: Faker, departments: list[dict]) -> list[dict]:
    instructors = []
    for dept in departments:
        for idx in range(1, 11):
            iid = f"{dept['departmentId']}-INST-{idx:03d}"
            instructors.append(
                {
                    "instructorId": iid,
                    "firstName": fake.first_name(),
                    "lastName": fake.last_name(),
                    "departmentId": dept["departmentId"],
                    "email": f"{iid.lower()}@university.edu",
                }
            )
    database.instructors.insert_many(instructors)
    return instructors


def seed_courses(database, departments: list[dict], instructors: list[dict], courses_per_dept: int) -> list[dict]:
    courses = []
    by_dept = {}
    for inst in instructors:
        by_dept.setdefault(inst["departmentId"], []).append(inst)

    for dept in departments:
        for idx in range(1, courses_per_dept + 1):
            cid = f"{dept['departmentId']}-{idx:03d}"
            assigned = random.choice(by_dept[dept["departmentId"]])
            courses.append(
                {
                    "courseId": cid,
                    "title": f"{dept['departmentId']} Course {idx}",
                    "departmentId": dept["departmentId"],
                    "credits": random.randint(2, 6),
                    "semesterOffered": random.choice(SEMESTERS),
                    "instructorId": assigned["instructorId"],
                }
            )
    database.courses.insert_many(courses)
    return courses


def seed_students(database, fake: Faker, count: int) -> list[dict]:
    students = []
    for idx in range(1, count + 1):
        dept = random.choice(DEPT_IDS)
        sid = f"{dept}-STU-{idx:06d}"
        students.append(
            {
                "studentId": sid,
                "firstName": fake.first_name(),
                "lastName": fake.last_name(),
                "email": f"{sid.lower()}@students.university.edu",
                "departmentId": dept,
                "group": f"{dept}-{random.randint(1, 15):02d}",
                "year": random.randint(1, 6),
                "enrolledAt": datetime.now(timezone.utc),
                "status": "active",
            }
        )
    database.students.insert_many(students)
    return students


def seed_enrollments_and_grades(database, students: list[dict], courses: list[dict]) -> tuple[int, int]:
    by_dept_courses = {}
    for course in courses:
        by_dept_courses.setdefault(course["departmentId"], []).append(course)

    enrollments = []
    grades = []
    enrollment_counter = 0
    grade_counter = 0

    for student in students:
        num_courses = random.randint(4, 8)
        pool = by_dept_courses[student["departmentId"]]
        selected = random.sample(pool, k=min(num_courses, len(pool)))
        for course in selected:
            enrollment_counter += 1
            enrollment_id = f"ENR-{enrollment_counter:010d}"
            semester = random.choice(SEMESTERS)
            enrollments.append(
                {
                    "enrollmentId": enrollment_id,
                    "departmentId": student["departmentId"],
                    "studentId": student["studentId"],
                    "courseId": course["courseId"],
                    "semester": semester,
                    "enrolledAt": datetime.now(timezone.utc),
                    "status": random.choice(["enrolled", "completed"]),
                }
            )

            if random.random() < 0.85:
                grade_counter += 1
                grades.append(
                    {
                        "gradeId": f"GRD-{grade_counter:010d}",
                        "studentId": student["studentId"],
                        "courseId": course["courseId"],
                        "semester": semester,
                        "grade": random.choice(GRADE_CHOICES),
                        "updatedAt": datetime.now(timezone.utc),
                    }
                )

    if enrollments:
        database.enrollments.insert_many(enrollments, ordered=False)
    if grades:
        database.grades.insert_many(grades, ordered=False)

    return len(enrollments), len(grades)


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    fake = Faker()
    Faker.seed(args.seed)

    client = MongoClient(args.mongo_uri)
    database = client[args.db_name]

    reset_collections(database)
    departments = seed_departments(database)
    instructors = seed_instructors(database, fake, departments)
    courses = seed_courses(database, departments, instructors, args.courses_per_dept)
    students = seed_students(database, fake, args.students)
    enr_count, grd_count = seed_enrollments_and_grades(database, students, courses)

    print("Seeding complete:")
    print(f"- departments: {len(departments)}")
    print(f"- instructors: {len(instructors)}")
    print(f"- courses: {len(courses)}")
    print(f"- students: {len(students)}")
    print(f"- enrollments: {enr_count}")
    print(f"- grades: {grd_count}")


if __name__ == "__main__":
    main()

