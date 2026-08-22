from pathlib import Path

from app.data_generator.config import GenerationConfig
from app.data_generator.export import export_dataset
from app.data_generator.generator import generate_data
from app.data_generator.quality import assert_quality, build_quality_report


def test_generation_is_deterministic() -> None:
    first = generate_data(GenerationConfig(student_count=120, club_count=45, activity_count=135))
    second = generate_data(GenerationConfig(student_count=120, club_count=45, activity_count=135))

    assert first.fingerprint() == second.fingerprint()
    assert first.counts() == second.counts()


def test_full_dataset_passes_quality_checks() -> None:
    graph = generate_data()

    report = assert_quality(graph)

    assert report["status"] == "passed"
    assert report["counts"]["students"] == 3000
    assert 18000 <= report["counts"]["activity_registrations"] <= 25000
    assert report["metrics"]["actual_participations"] >= 15000


def test_quality_report_detects_duplicate_registration() -> None:
    graph = generate_data(GenerationConfig(student_count=120, club_count=45, activity_count=135))
    graph.tables["activity_registrations"].append(dict(graph.tables["activity_registrations"][0]))

    report = build_quality_report(graph)

    assert report["checks"]["unique_registrations_pair"]["passed"] is False


def test_csv_export_matches_graph_counts(tmp_path: Path) -> None:
    graph = generate_data(GenerationConfig(student_count=120, club_count=45, activity_count=135))
    report = build_quality_report(graph)

    files = export_dataset(graph, report, tmp_path / "generated")

    students_file = tmp_path / "generated" / "students.csv"
    assert students_file in files
    assert len(students_file.read_text(encoding="utf-8-sig").splitlines()) == 121
    assert (tmp_path / "generated" / "data_quality_report.json").exists()
