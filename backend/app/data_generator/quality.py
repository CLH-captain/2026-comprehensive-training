from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from app.data_generator.generator import DataGraph, Row


def _result(passed: bool, message: str, value: Any = None) -> dict[str, Any]:
    return {"passed": passed, "message": message, "value": value}


def _ids(rows: list[Row]) -> set[int]:
    return {row["id"] for row in rows}


def build_quality_report(graph: DataGraph) -> dict[str, Any]:
    tables = graph.tables
    checks: dict[str, dict[str, Any]] = {}
    counts = graph.counts()
    expected_ranges = {
        "campuses": (2, 2),
        "academic_terms": (2, 2),
        "colleges": (10, 14),
        "majors": (35, 50),
        "students": (3000, 3000),
        "club_categories": (6, 6),
        "clubs": (40, 50),
        "club_memberships": (3500, 5000),
        "activity_categories": (7, 7),
        "venues": (20, 30),
        "activities": (300, 350),
        "activity_registrations": (18000, 25000),
        "activity_attendance": (16000, 22000),
    }
    for name, (minimum, maximum) in expected_ranges.items():
        value = counts.get(name, 0)
        checks[f"count_{name}"] = _result(
            minimum <= value <= maximum,
            f"{name} count must be between {minimum} and {maximum}",
            value,
        )

    campus_ids = _ids(tables["campuses"])
    college_ids = _ids(tables["colleges"])
    major_ids = _ids(tables["majors"])
    student_ids = _ids(tables["students"])
    club_ids = _ids(tables["clubs"])
    activity_ids = _ids(tables["activities"])
    registration_ids = _ids(tables["activity_registrations"])
    term_ids = _ids(tables["academic_terms"])
    venue_ids = _ids(tables["venues"])
    activity_category_ids = _ids(tables["activity_categories"])
    club_category_ids = _ids(tables["club_categories"])

    references_valid = all(row["primary_campus_id"] in campus_ids for row in tables["colleges"])
    references_valid &= all(row["college_id"] in college_ids for row in tables["majors"])
    references_valid &= all(
        row["college_id"] in college_ids and row["major_id"] in major_ids
        for row in tables["students"]
    )
    references_valid &= all(
        row["category_id"] in club_category_ids
        and row["home_campus_id"] in campus_ids
        and row["leader_student_id"] in student_ids
        for row in tables["clubs"]
    )
    references_valid &= all(
        row["club_id"] in club_ids and row["student_id"] in student_ids
        for row in tables["club_memberships"]
    )
    references_valid &= all(
        row["club_id"] in club_ids
        and row["category_id"] in activity_category_ids
        and row["term_id"] in term_ids
        and row["venue_id"] in venue_ids
        for row in tables["activities"]
    )
    references_valid &= all(
        row["activity_id"] in activity_ids and row["student_id"] in student_ids
        for row in tables["activity_registrations"]
    )
    references_valid &= all(
        row["activity_id"] in activity_ids
        and row["student_id"] in student_ids
        and row["registration_id"] in registration_ids
        for row in tables["activity_attendance"]
    )
    checks["foreign_keys"] = _result(references_valid, "all generated references must exist")

    unique_specs = {
        "students_student_no": (tables["students"], lambda row: row["student_no"]),
        "clubs_code": (tables["clubs"], lambda row: row["code"]),
        "activities_code": (tables["activities"], lambda row: row["code"]),
        "memberships_pair": (tables["club_memberships"], lambda row: (row["club_id"], row["student_id"])),
        "registrations_pair": (tables["activity_registrations"], lambda row: (row["activity_id"], row["student_id"])),
        "attendance_pair": (tables["activity_attendance"], lambda row: (row["activity_id"], row["student_id"])),
    }
    for name, (rows, key_function) in unique_specs.items():
        keys = [key_function(row) for row in rows]
        checks[f"unique_{name}"] = _result(len(keys) == len(set(keys)), f"{name} must be unique")

    activity_by_id = {row["id"]: row for row in tables["activities"]}
    time_valid = all(row["start_time"] < row["end_time"] for row in tables["activities"])
    time_valid &= all(
        row["register_time"] < activity_by_id[row["activity_id"]]["start_time"]
        for row in tables["activity_registrations"]
    )
    time_valid &= all(
        row["checkin_time"] is None
        or activity_by_id[row["activity_id"]]["start_time"] - timedelta(minutes=35)
        <= row["checkin_time"]
        <= activity_by_id[row["activity_id"]]["start_time"] + timedelta(minutes=35)
        for row in tables["activity_attendance"]
    )
    checks["time_consistency"] = _result(time_valid, "registration and check-in times must be valid")

    valid_registrations: Counter[int] = Counter(
        row["activity_id"]
        for row in tables["activity_registrations"]
        if row["status"] == "registered"
    )
    capacity_valid = all(valid_registrations[row["id"]] <= row["capacity"] for row in tables["activities"])
    checks["capacity"] = _result(capacity_valid, "valid registrations must not exceed activity capacity")

    grade_counts = Counter(row["grade_no"] for row in tables["students"])
    grade_ratios = {str(grade): round(count / len(tables["students"]), 4) for grade, count in sorted(grade_counts.items())}
    expected_grade_ratios = {1: 0.27, 2: 0.27, 3: 0.25, 4: 0.21}
    grade_valid = all(abs(grade_counts[grade] / len(tables["students"]) - expected) <= 0.01 for grade, expected in expected_grade_ratios.items())
    checks["grade_distribution"] = _result(grade_valid, "grade distribution must match the configured profile", grade_ratios)

    member_counts = Counter(row["club_id"] for row in tables["club_memberships"])
    member_values = list(member_counts.values())
    long_tail_ratio = round(max(member_values) / min(member_values), 2)
    checks["club_member_long_tail"] = _result(long_tail_ratio >= 2.0, "largest club must have at least twice the members of the smallest", long_tail_ratio)

    size_counts = Counter()
    for row in tables["activities"]:
        capacity = row["capacity"]
        if capacity <= 40:
            size_counts["small"] += 1
        elif capacity <= 100:
            size_counts["medium"] += 1
        elif capacity <= 250:
            size_counts["large"] += 1
        else:
            size_counts["extra_large"] += 1
    activity_total = len(tables["activities"])
    size_ratios = {name: round(size_counts[name] / activity_total, 4) for name in ("small", "medium", "large", "extra_large")}
    size_valid = 0.32 <= size_ratios["small"] <= 0.48 and 0.32 <= size_ratios["medium"] <= 0.48 and 0.11 <= size_ratios["large"] <= 0.23 and 0.01 <= size_ratios["extra_large"] <= 0.06
    checks["activity_size_distribution"] = _result(size_valid, "activity sizes must follow the configured mixed distribution", size_ratios)

    month_counts = Counter(row["start_time"].month for row in tables["activities"])
    autumn = sum(month_counts[month] for month in (9, 10, 11)) / 3
    winter = sum(month_counts[month] for month in (1, 2)) / 2
    spring = sum(month_counts[month] for month in (3, 4, 5)) / 3
    trend_valid = autumn > winter * 2 and spring > winter * 2
    checks["monthly_trend"] = _result(trend_valid, "autumn and spring activity peaks must exceed winter vacation", dict(sorted(month_counts.items())))

    attendance_counts = Counter(row["status"] for row in tables["activity_attendance"])
    attendance_total = len(tables["activity_attendance"])
    attended = attendance_counts["present"] + attendance_counts["late"]
    attendance_rate = round(attended / attendance_total, 4) if attendance_total else 0
    late_rate = round(attendance_counts["late"] / attended, 4) if attended else 0
    checks["attendance_rate"] = _result(0.75 <= attendance_rate <= 0.92, "overall attendance rate must be between 75% and 92%", attendance_rate)
    checks["late_rate"] = _result(0.03 <= late_rate <= 0.08, "late arrivals must be 3% to 8% of attendees", late_rate)
    checks["actual_participations"] = _result(attended >= 15000, "present and late records must reach the acceptance minimum", attended)

    cancelled_activities = sum(row["status"] == "cancelled" for row in tables["activities"])
    activity_cancel_rate = round(cancelled_activities / activity_total, 4)
    cancelled_registrations = sum(row["status"] == "cancelled" for row in tables["activity_registrations"])
    registration_cancel_rate = round(cancelled_registrations / len(tables["activity_registrations"]), 4)
    checks["activity_cancel_rate"] = _result(0.02 <= activity_cancel_rate <= 0.04, "cancelled activities must be 2% to 4%", activity_cancel_rate)
    checks["registration_cancel_rate"] = _result(0.05 <= registration_cancel_rate <= 0.11, "cancelled registrations must remain a realistic minority", registration_cancel_rate)

    all_passed = all(check["passed"] for check in checks.values())
    return {
        "status": "passed" if all_passed else "failed",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "seed": graph.seed,
        "fingerprint": graph.fingerprint(),
        "counts": counts,
        "metrics": {
            "attendance_rate": attendance_rate,
            "late_rate": late_rate,
            "actual_participations": attended,
            "activity_cancel_rate": activity_cancel_rate,
            "registration_cancel_rate": registration_cancel_rate,
            "activity_size_distribution": size_ratios,
            "club_member_min": min(member_values),
            "club_member_max": max(member_values),
        },
        "checks": checks,
    }


def assert_quality(graph: DataGraph) -> dict[str, Any]:
    report = build_quality_report(graph)
    if report["status"] != "passed":
        failures = [name for name, check in report["checks"].items() if not check["passed"]]
        raise ValueError(f"generated data failed quality checks: {', '.join(failures)}")
    return report
