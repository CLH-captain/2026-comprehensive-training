from __future__ import annotations

import csv
import json
import os
import shutil
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.data_generator.generator import DataGraph


def _serialize(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, bool):
        return int(value)
    return value


def export_dataset(graph: DataGraph, report: dict[str, Any], output_dir: Path) -> list[Path]:
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix="szut-data-", dir=output_dir.parent))
    written_names: list[str] = []
    try:
        for table_name, rows in graph.tables.items():
            if not rows:
                continue
            file_path = staging / f"{table_name}.csv"
            with file_path.open("w", encoding="utf-8-sig", newline="") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(
                    {key: _serialize(value) for key, value in row.items()}
                    for row in rows
                )
            written_names.append(file_path.name)
        report_path = staging / "data_quality_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        written_names.append(report_path.name)

        output_dir.mkdir(parents=True, exist_ok=True)
        for name in written_names:
            os.replace(staging / name, output_dir / name)
        return [output_dir / name for name in written_names]
    finally:
        shutil.rmtree(staging, ignore_errors=True)
