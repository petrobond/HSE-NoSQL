#!/usr/bin/env python3
"""Simple CLI for the university MongoDB dataset."""

from __future__ import annotations

import argparse
import statistics
import time
from dataclasses import dataclass
from datetime import UTC, datetime

from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


GRADE_POINTS = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}


@dataclass
class AppContext:
    db_name: str
    client: MongoClient

    @property
    def db(self):
        return self.client[self.db_name]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="University DB CLI")
    parser.add_argument("--mongo-uri", required=True, help="MongoDB connection URI")
    parser.add_argument("--db-name", default="university", help="Database name")

    sub = parser.add_subparsers(dest="command", required=True)

    create_student = sub.add_parser("create-student", help="Create a student")
    create_student.add_argument("--student-id", required=True)
    create_student.add_argument("--first-name", required=True)
    create_student.add_argument("--last-name", required=True)
    create_student.add_argument("--email", required=True)
    create_student.add_argument("--department-id", required=True)
    create_student.add_argument("--group", required=True)
    create_student.add_argument("--year", type=int, required=True)

    find_student = sub.add_parser("find-student", help="Find student by ID")
    find_student.add_argument("--student-id", required=True)

    enroll = sub.add_parser("enroll", help="Enroll student to course")
    enroll.add_argument("--enrollment-id", required=True)
    enroll.add_argument("--department-id", required=True)
    enroll.add_argument("--student-id", required=True)
    enroll.add_argument("--course-id", required=True)
    enroll.add_argument("--semester", required=True)

    grade = sub.add_parser("add-grade", help="Add grade for student course")
    grade.add_argument("--grade-id", required=True)
    grade.add_argument("--student-id", required=True)
    grade.add_argument("--course-id", required=True)
    grade.add_argument("--semester", required=True)
    grade.add_argument("--grade", required=True, choices=list(GRADE_POINTS.keys()) + ["Pass", "Fail"])

    report = sub.add_parser("student-report", help="Student performance report")
    report.add_argument("--student-id", required=True)

    return parser


def timed(label: str, fn):
    start = time.perf_counter()
    value = fn()
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"{label} completed in {elapsed_ms:.2f} ms")
    return value


def cmd_create_student(ctx: AppContext, args: argparse.Namespace) -> None:
    if not 1 <= args.year <= 6:
        raise ValueError("Year must be in range [1, 6]")

    doc = {
        "studentId": args.student_id,
        "firstName": args.first_name,
        "lastName": args.last_name,
        "email": args.email,
        "departmentId": args.department_id,
        "group": args.group,
        "year": args.year,
        "enrolledAt": datetime.now(UTC),
        "status": "active",
    }

    try:
        timed("create-student", lambda: ctx.db.students.insert_one(doc))
    except DuplicateKeyError as err:
        raise ValueError(f"Student already exists or email is duplicated: {err.details}") from err

    print("Student created.")


def cmd_find_student(ctx: AppContext, args: argparse.Namespace) -> None:
    student = timed(
        "find-student",
        lambda: ctx.db.students.find_one({"studentId": args.student_id}, {"_id": 0}),
    )
    if not student:
        print("Student not found.")
        return
    print(student)


def cmd_enroll(ctx: AppContext, args: argparse.Namespace) -> None:
    student = ctx.db.students.find_one({"studentId": args.student_id}, {"_id": 0, "departmentId": 1})
    if not student:
        raise ValueError("Cannot enroll: student not found")
    if student["departmentId"] != args.department_id:
        raise ValueError("department-id must match student's departmentId for this shard strategy")

    course = ctx.db.courses.find_one({"courseId": args.course_id}, {"_id": 0})
    if not course:
        raise ValueError("Cannot enroll: course not found")

    doc = {
        "enrollmentId": args.enrollment_id,
        "departmentId": args.department_id,
        "studentId": args.student_id,
        "courseId": args.course_id,
        "semester": args.semester,
        "enrolledAt": datetime.now(UTC),
        "status": "enrolled",
    }

    try:
        timed("enroll", lambda: ctx.db.enrollments.insert_one(doc))
    except DuplicateKeyError as err:
        raise ValueError(f"Enrollment ID already exists: {err.details}") from err
    print("Enrollment created.")


def cmd_add_grade(ctx: AppContext, args: argparse.Namespace) -> None:
    enrollment = ctx.db.enrollments.find_one(
        {"studentId": args.student_id, "courseId": args.course_id, "semester": args.semester},
        {"_id": 0},
    )
    if not enrollment:
        raise ValueError("No enrollment found for this student/course/semester")

    doc = {
        "gradeId": args.grade_id,
        "studentId": args.student_id,
        "courseId": args.course_id,
        "semester": args.semester,
        "grade": args.grade,
        "updatedAt": datetime.now(UTC),
    }
    try:
        timed("add-grade", lambda: ctx.db.grades.insert_one(doc))
    except DuplicateKeyError as err:
        raise ValueError(f"Grade ID already exists: {err.details}") from err
    print("Grade recorded.")


def cmd_student_report(ctx: AppContext, args: argparse.Namespace) -> None:
    student = ctx.db.students.find_one({"studentId": args.student_id}, {"_id": 0})
    if not student:
        print("Student not found.")
        return

    enrollments = timed(
        "load-enrollments",
        lambda: list(ctx.db.enrollments.find({"studentId": args.student_id}, {"_id": 0})),
    )
    grades = timed(
        "load-grades",
        lambda: list(ctx.db.grades.find({"studentId": args.student_id}, {"_id": 0})),
    )

    points = [GRADE_POINTS[g["grade"]] for g in grades if g["grade"] in GRADE_POINTS]
    avg_score = statistics.mean(points) if points else None

    print("=== Student Report ===")
    print(f"Student: {student['studentId']} {student['firstName']} {student['lastName']}")
    print(f"Department: {student['departmentId']}, Year: {student['year']}, Group: {student['group']}")
    print(f"Enrollments: {len(enrollments)}")
    print(f"Grades: {len(grades)}")
    print(f"Average score (5-point scale): {avg_score:.2f}" if avg_score else "Average score: N/A")

    if grades:
        print("Recent grades:")
        for grade in grades[:10]:
            print(
                f"- {grade['semester']} {grade['courseId']} -> {grade['grade']}"
            )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    ctx = AppContext(db_name=args.db_name, client=MongoClient(args.mongo_uri))

    commands = {
        "create-student": cmd_create_student,
        "find-student": cmd_find_student,
        "enroll": cmd_enroll,
        "add-grade": cmd_add_grade,
        "student-report": cmd_student_report,
    }

    try:
        commands[args.command](ctx, args)
    except ValueError as err:
        parser.error(str(err))


if __name__ == "__main__":
    main()

