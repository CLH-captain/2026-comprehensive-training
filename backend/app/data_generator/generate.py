from __future__ import annotations

import argparse
from pathlib import Path

from app.core.config import get_settings
from app.data_generator.config import DEFAULT_SEED, GenerationConfig
from app.data_generator.export import export_dataset
from app.data_generator.generator import generate_data
from app.data_generator.quality import assert_quality
from app.data_generator.seed import assert_project_database_url, seed_database
from app.db.session import create_engine_from_url


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the deterministic SZUT club dataset")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--database", choices=("development", "test"), default="development")
    parser.add_argument("--reset", action="store_true", help="clear the selected project database before seeding")
    parser.add_argument("--export-only", action="store_true", help="skip MySQL and only export CSV/report")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[3] / "data" / "generated")
    return parser


def main() -> None:
    args = _parser().parse_args()
    settings = get_settings()
    database_url = settings.database_url if args.database == "development" else settings.test_database_url
    assert_project_database_url(database_url)

    graph = generate_data(GenerationConfig(seed=args.seed))
    report = assert_quality(graph)
    files = export_dataset(graph, report, args.output.resolve())
    if not args.export_only:
        engine = create_engine_from_url(database_url)
        try:
            seed_database(engine, database_url, graph, reset=args.reset)
        finally:
            engine.dispose()

    counts = report["counts"]
    print(
        "dataset ready: "
        f"students={counts['students']}, clubs={counts['clubs']}, "
        f"activities={counts['activities']}, registrations={counts['activity_registrations']}, "
        f"attendance={counts['activity_attendance']}, quality={report['status']}, files={len(files)}"
    )


if __name__ == "__main__":
    main()
