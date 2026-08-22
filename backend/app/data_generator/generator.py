from __future__ import annotations

import calendar
import hashlib
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any

from faker import Faker

from app.data_generator.config import (
    ACTIVITY_CATEGORIES,
    CAMPUSES,
    CLUB_CATEGORIES,
    CLUB_NAMES,
    CLUB_TO_ACTIVITY_CATEGORY,
    COLLEGE_ACTIVITY_PREFERENCES,
    COLLEGES,
    GRADE_PARTICIPATION,
    GRADE_WEIGHTS,
    MEMBERSHIP_COUNT_WEIGHTS,
    MONTH_WEIGHTS,
    GenerationConfig,
)

Row = dict[str, Any]


@dataclass(frozen=True)
class DataGraph:
    seed: int
    tables: dict[str, list[Row]]
    metadata: dict[str, Any]

    def counts(self) -> dict[str, int]:
        return {name: len(rows) for name, rows in self.tables.items()}

    def fingerprint(self) -> str:
        digest = hashlib.sha256()
        digest.update(str(self.seed).encode())
        for table_name in sorted(self.tables):
            digest.update(table_name.encode())
            for row in self.tables[table_name]:
                digest.update(repr(sorted(row.items())).encode("utf-8"))
        return digest.hexdigest()


def _allocate(total: int, weights: list[float], minimum: int = 0) -> list[int]:
    remaining = total - minimum * len(weights)
    if remaining < 0:
        raise ValueError("total is smaller than the requested minimum allocation")
    weight_sum = sum(weights)
    raw = [remaining * weight / weight_sum for weight in weights]
    values = [minimum + math.floor(value) for value in raw]
    missing = total - sum(values)
    order = sorted(range(len(raw)), key=lambda index: (raw[index] % 1, -index), reverse=True)
    for index in order[:missing]:
        values[index] += 1
    return values


def _weighted_sample(
    rng: random.Random,
    items: list[int],
    weights: list[float],
    count: int,
) -> list[int]:
    if count >= len(items):
        return list(items)
    scored = [
        (math.log(max(rng.random(), 1e-12)) / max(weight, 1e-6), item)
        for item, weight in zip(items, weights, strict=True)
    ]
    scored.sort(reverse=True)
    return [item for _, item in scored[:count]]


def _student_name(fake: Faker, index: int) -> str:
    return f"{fake.name()}{index:04d}" if index % 431 == 0 else fake.name()


def _build_foundation(
    config: GenerationConfig,
    rng: random.Random,
    fake: Faker,
) -> tuple[dict[str, list[Row]], dict[str, Any]]:
    tables: dict[str, list[Row]] = {}
    campuses = [
        {"id": index, "code": code, "name": name, "address": address, "is_active": True}
        for index, (code, name, address) in enumerate(CAMPUSES, 1)
    ]
    tables["campuses"] = campuses
    campus_ids = {row["code"]: row["id"] for row in campuses}

    terms = [
        {
            "id": 1,
            "academic_year": "2025-2026",
            "term_no": 1,
            "name": "2025-2026学年第一学期",
            "start_date": date(2025, 9, 1),
            "end_date": date(2026, 1, 18),
            "is_default": False,
        },
        {
            "id": 2,
            "academic_year": "2025-2026",
            "term_no": 2,
            "name": "2025-2026学年第二学期",
            "start_date": date(2026, 2, 23),
            "end_date": date(2026, 7, 5),
            "is_default": True,
        },
    ]
    tables["academic_terms"] = terms

    college_counts = _allocate(
        config.student_count,
        [college[3] for college in COLLEGES],
    )
    colleges: list[Row] = []
    majors: list[Row] = []
    major_id = 1
    college_major_ids: dict[int, list[int]] = {}
    for college_id, (code, name, campus_code, _, major_names) in enumerate(COLLEGES, 1):
        colleges.append(
            {
                "id": college_id,
                "code": code,
                "name": name,
                "primary_campus_id": campus_ids[campus_code],
                "is_active": True,
            }
        )
        college_major_ids[college_id] = []
        for local_index, major_name in enumerate(major_names, 1):
            majors.append(
                {
                    "id": major_id,
                    "code": f"{code}{local_index:02d}",
                    "college_id": college_id,
                    "name": major_name,
                    "duration_years": 4,
                    "is_active": True,
                }
            )
            college_major_ids[college_id].append(major_id)
            major_id += 1
    tables["colleges"] = colleges
    tables["majors"] = majors

    grade_counts = _allocate(config.student_count, list(GRADE_WEIGHTS))
    grades = [grade for grade, count in enumerate(grade_counts, 1) for _ in range(count)]
    rng.shuffle(grades)
    college_sequence = [
        college_id
        for college_id, count in enumerate(college_counts, 1)
        for _ in range(count)
    ]
    rng.shuffle(college_sequence)
    students: list[Row] = []
    for student_id, (college_id, grade) in enumerate(zip(college_sequence, grades, strict=True), 1):
        major_id_value = rng.choice(college_major_ids[college_id])
        enrollment_year = 2026 - grade
        students.append(
            {
                "id": student_id,
                "student_no": f"{enrollment_year}{college_id:02d}{student_id:05d}",
                "name": _student_name(fake, student_id),
                "gender": "男" if rng.random() < 0.52 else "女",
                "college_id": college_id,
                "major_id": major_id_value,
                "enrollment_year": enrollment_year,
                "grade_no": grade,
                "class_name": f"{next(row['name'] for row in majors if row['id'] == major_id_value)}{enrollment_year % 100:02d}-{rng.randint(1, 4)}班",
                "status": "active",
                "created_at": datetime.combine(date(2025, 8, 20), time(9, 0)),
            }
        )
    tables["students"] = students

    tables["club_categories"] = [
        {"id": index, "name": name, "description": f"{name}类学生社团", "is_active": True}
        for index, name in enumerate(CLUB_CATEGORIES, 1)
    ]
    tables["activity_categories"] = [
        {"id": index, "name": name, "description": f"{name}主题活动", "is_active": True}
        for index, name in enumerate(ACTIVITY_CATEGORIES, 1)
    ]

    venues: list[Row] = []
    venue_templates = (
        ("社团活动室", 45, "activity_room"),
        ("研讨教室", 70, "classroom"),
        ("多功能厅", 120, "hall"),
        ("报告厅", 220, "auditorium"),
        ("大学生活动中心", 360, "activity_center"),
        ("体育馆", 800, "gymnasium"),
        ("田径场", 1200, "stadium"),
        ("篮球场", 100, "sports_field"),
        ("羽毛球馆", 80, "sports_field"),
        ("图书馆报告厅", 260, "auditorium"),
        ("创新工坊", 90, "workshop"),
        ("艺术实践中心", 180, "studio"),
    )
    for campus in campuses:
        for local_index, (name, capacity, venue_type) in enumerate(venue_templates, 1):
            venues.append(
                {
                    "id": len(venues) + 1,
                    "code": f"{campus['code']}-V{local_index:02d}",
                    "campus_id": campus["id"],
                    "name": f"{campus['name']}{name}",
                    "capacity": capacity,
                    "venue_type": venue_type,
                    "is_active": True,
                }
            )
    tables["venues"] = venues
    return tables, {
        "college_counts": dict(zip((item[0] for item in COLLEGES), college_counts, strict=True)),
        "grade_counts": dict(enumerate(grade_counts, 1)),
    }


def _build_clubs_and_memberships(
    tables: dict[str, list[Row]],
    config: GenerationConfig,
    rng: random.Random,
    fake: Faker,
) -> tuple[dict[int, set[int]], dict[int, tuple[float, float, float]]]:
    popularity = [0.62 + 1.38 * (1 - index / config.club_count) ** 1.7 for index in range(config.club_count)]
    rng.shuffle(popularity)
    activity_level = [rng.uniform(0.5, 1.5) for _ in range(config.club_count)]
    engagement = [rng.uniform(0.6, 1.3) for _ in range(config.club_count)]
    clubs: list[Row] = []
    for index, ((name, category_index), popularity_value) in enumerate(zip(CLUB_NAMES, popularity, strict=True), 1):
        home_campus_id = 1 if (index + category_index) % 5 < 3 else 2
        clubs.append(
            {
                "id": index,
                "code": f"CLUB{index:03d}",
                "name": name,
                "category_id": category_index + 1,
                "home_campus_id": home_campus_id,
                "advisor_name": fake.name(),
                "leader_student_id": None,
                "founded_date": date(rng.randint(2012, 2024), rng.randint(1, 12), rng.randint(1, 25)),
                "description": f"面向全校学生开展{name}相关交流、实践与校园文化活动。",
                "status": "active",
            }
        )
    tables["clubs"] = clubs

    count_sequence = [
        count
        for count, weight in MEMBERSHIP_COUNT_WEIGHTS
        for _ in range(round(config.student_count * weight))
    ]
    count_sequence = count_sequence[: config.student_count]
    while len(count_sequence) < config.student_count:
        count_sequence.append(1)
    rng.shuffle(count_sequence)
    club_ids = list(range(1, config.club_count + 1))
    club_members: dict[int, set[int]] = defaultdict(set)
    student_clubs: dict[int, set[int]] = defaultdict(set)
    for student_id, desired_count in enumerate(count_sequence, 1):
        selected = _weighted_sample(rng, club_ids, popularity, desired_count)
        for club_id in selected:
            club_members[club_id].add(student_id)
            student_clubs[student_id].add(club_id)

    for club_id in club_ids:
        if not club_members[club_id]:
            student_id = rng.randint(1, config.student_count)
            club_members[club_id].add(student_id)
            student_clubs[student_id].add(club_id)

    memberships: list[Row] = []
    membership_id = 1
    for club in clubs:
        members = sorted(club_members[club["id"]])
        leader_id = rng.choice(members)
        club["leader_student_id"] = leader_id
        core_count = max(2, round(len(members) * 0.08))
        core_members = set(rng.sample(members, min(core_count, len(members))))
        for student_id in members:
            role = "leader" if student_id == leader_id else ("core" if student_id in core_members else "member")
            memberships.append(
                {
                    "id": membership_id,
                    "club_id": club["id"],
                    "student_id": student_id,
                    "role": role,
                    "join_date": date(rng.randint(2022, 2025), rng.randint(3, 11), rng.randint(1, 25)),
                    "status": "active",
                }
            )
            membership_id += 1
    tables["club_memberships"] = memberships
    generation_metrics = {
        club_id: (
            popularity[club_id - 1],
            activity_level[club_id - 1],
            engagement[club_id - 1],
        )
        for club_id in club_ids
    }
    return dict(club_members), generation_metrics


def _activity_datetime(rng: random.Random) -> tuple[int, datetime]:
    months = list(MONTH_WEIGHTS)
    month = rng.choices(months, weights=[MONTH_WEIGHTS[value] for value in months], k=1)[0]
    year = 2025 if month >= 9 else 2026
    first_day = 1
    last_day = calendar.monthrange(year, month)[1]
    if month == 1:
        last_day = 17
    elif month == 2:
        first_day = 23
    day = rng.randint(first_day, last_day)
    hour = rng.choice((9, 10, 14, 15, 18, 19))
    start = datetime.combine(date(year, month, day), time(hour, rng.choice((0, 30))))
    return (1 if month >= 9 or month == 1 else 2), start


def _activity_capacity(rng: random.Random) -> int:
    roll = rng.random()
    if roll < 0.40:
        return rng.randint(18, 40)
    if roll < 0.80:
        return rng.randint(45, 90)
    if roll < 0.97:
        return rng.randint(100, 180)
    return rng.randint(260, 400)


def _build_activities(
    tables: dict[str, list[Row]],
    config: GenerationConfig,
    rng: random.Random,
    metrics: dict[int, tuple[float, float, float]],
) -> None:
    activity_counts = _allocate(
        config.activity_count,
        [metrics[club_id][1] for club_id in range(1, config.club_count + 1)],
        minimum=3,
    )
    club_rows = {row["id"]: row for row in tables["clubs"]}
    venues = tables["venues"]
    activities: list[Row] = []
    title_suffixes = ("交流会", "体验日", "主题实践", "校园挑战赛", "成果分享会", "训练营", "专题讲座", "联合行动")
    for club_id, count in enumerate(activity_counts, 1):
        club = club_rows[club_id]
        base_category_id = CLUB_TO_ACTIVITY_CATEGORY[club["category_id"] - 1] + 1
        for local_index in range(1, count + 1):
            capacity = _activity_capacity(rng)
            campus_id = club["home_campus_id"] if rng.random() < 0.78 else 3 - club["home_campus_id"]
            candidates = [row for row in venues if row["campus_id"] == campus_id and row["capacity"] >= capacity]
            venue = rng.choice(candidates)
            term_id, start = _activity_datetime(rng)
            duration_minutes = rng.choice((60, 90, 120, 150, 180))
            category_id = base_category_id if rng.random() < 0.82 else rng.randint(1, len(ACTIVITY_CATEGORIES))
            cancelled = rng.random() < 0.03
            activities.append(
                {
                    "id": len(activities) + 1,
                    "code": f"ACT{len(activities) + 1:04d}",
                    "club_id": club_id,
                    "category_id": category_id,
                    "term_id": term_id,
                    "venue_id": venue["id"],
                    "title": f"{club['name']}·{rng.choice(title_suffixes)}{local_index:02d}",
                    "description": f"由{club['name']}组织的{ACTIVITY_CATEGORIES[category_id - 1]}主题校园活动。",
                    "start_time": start,
                    "end_time": start + timedelta(minutes=duration_minutes),
                    "capacity": capacity,
                    "status": "cancelled" if cancelled else "completed",
                    "created_at": start - timedelta(days=rng.randint(14, 45)),
                }
            )
    rng.shuffle(activities)
    for activity_id, activity in enumerate(activities, 1):
        activity["id"] = activity_id
        activity["code"] = f"ACT{activity_id:04d}"
    tables["activities"] = activities


def _build_participation(
    tables: dict[str, list[Row]],
    rng: random.Random,
    club_members: dict[int, set[int]],
    metrics: dict[int, tuple[float, float, float]],
) -> None:
    students = tables["students"]
    student_ids = [row["id"] for row in students]
    college_codes = {row["id"]: row["code"] for row in tables["colleges"]}
    student_by_id = {row["id"]: row for row in students}
    registrations: list[Row] = []
    attendance: list[Row] = []
    registration_id = 1
    attendance_id = 1
    for activity in tables["activities"]:
        club_id = activity["club_id"]
        popularity, _, engagement = metrics[club_id]
        occupancy = min(0.99, max(0.72, 0.91 + (popularity - 1.0) * 0.10 + rng.uniform(-0.06, 0.06)))
        desired = max(8, min(activity["capacity"], round(activity["capacity"] * occupancy)))
        weights: list[float] = []
        category_index = activity["category_id"] - 1
        for student in students:
            college_code = college_codes[student["college_id"]]
            weight = GRADE_PARTICIPATION[student["grade_no"]]
            weight *= COLLEGE_ACTIVITY_PREFERENCES[college_code][category_index]
            weight *= popularity
            if student["id"] in club_members[club_id]:
                weight *= 2.45
            weights.append(weight * rng.uniform(0.82, 1.18))
        selected = _weighted_sample(rng, student_ids, weights, desired)
        for student_id in selected:
            cancelled_activity = activity["status"] == "cancelled"
            registration_cancelled = cancelled_activity or rng.random() < 0.07
            register_days = rng.randint(2, 28)
            register_time = activity["start_time"] - timedelta(days=register_days, hours=rng.randint(0, 12))
            registrations.append(
                {
                    "id": registration_id,
                    "activity_id": activity["id"],
                    "student_id": student_id,
                    "register_time": register_time,
                    "status": "cancelled" if registration_cancelled else "registered",
                    "source": "generated",
                }
            )
            if not registration_cancelled:
                is_member = student_id in club_members[club_id]
                base_attendance = 0.79 + (engagement - 0.95) * 0.09 + (0.075 if is_member else 0)
                base_attendance += (GRADE_PARTICIPATION[student_by_id[student_id]["grade_no"]] - 1) * 0.04
                attended = rng.random() < min(0.92, max(0.75, base_attendance))
                late = attended and rng.random() < 0.055
                status = "late" if late else ("present" if attended else "absent")
                if status == "present":
                    checkin_time = activity["start_time"] + timedelta(minutes=rng.randint(-30, 4))
                elif status == "late":
                    checkin_time = activity["start_time"] + timedelta(minutes=rng.randint(5, 30))
                else:
                    checkin_time = None
                attendance.append(
                    {
                        "id": attendance_id,
                        "activity_id": activity["id"],
                        "student_id": student_id,
                        "registration_id": registration_id,
                        "status": status,
                        "checkin_time": checkin_time,
                    }
                )
                attendance_id += 1
            registration_id += 1
    tables["activity_registrations"] = registrations
    tables["activity_attendance"] = attendance


def generate_data(config: GenerationConfig | None = None) -> DataGraph:
    config = config or GenerationConfig()
    rng = random.Random(config.seed)
    fake = Faker("zh_CN")
    fake.seed_instance(config.seed)
    tables, metadata = _build_foundation(config, rng, fake)
    club_members, metrics = _build_clubs_and_memberships(tables, config, rng, fake)
    _build_activities(tables, config, rng, metrics)
    _build_participation(tables, rng, club_members, metrics)
    metadata["club_member_counts"] = {
        club_id: len(members) for club_id, members in club_members.items()
    }
    metadata["club_generation_metrics"] = {
        club_id: {
            "popularity": values[0],
            "activity_level": values[1],
            "member_engagement": values[2],
        }
        for club_id, values in metrics.items()
    }
    metadata["activity_month_counts"] = dict(
        Counter(row["start_time"].month for row in tables["activities"])
    )
    return DataGraph(seed=config.seed, tables=tables, metadata=metadata)
