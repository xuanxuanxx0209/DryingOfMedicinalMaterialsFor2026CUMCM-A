from __future__ import annotations

import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "支撑材料"


def digest(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
    }


inputs = sorted((ROOT / "problem A" / "附件").rglob("*"))
sources = sorted(ROOT.glob("*.py"))
sources += sorted((ROOT / "figure_tools").glob("*.py"))
sources += sorted((ROOT / "utils").glob("*.py"))

manifest = {
    "schema_version": 1,
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "purpose": "CUMCM 2026 A题支撑材料的相对路径复现清单",
    "random_seed": 0,
    "runtime": {
        "python": platform.python_version(),
        "platform": platform.platform(),
    },
    "input_files": [digest(path) for path in inputs if path.is_file()],
    "source_files": [digest(path) for path in sources if path.is_file()],
    "quick_checks": [
        "python -X utf8 药材烘干求解.py --mode smoke",
        "python -X utf8 全程干燥求解.py --mode smoke",
        "python -X utf8 全程干燥求解.py --mode q3-smoke",
        "python -X utf8 问题4_求解.py --smoke --output results/P1_q4_smoke.json",
    ],
    "full_reproduction": [
        "python -X utf8 药材烘干求解.py --mode q1",
        "python -X utf8 全程干燥求解.py --mode q2",
        "python -X utf8 全程干燥求解.py --mode q3",
        "python -X utf8 问题4_复现.py --output-root .",
    ],
    "principal_outputs": [
        "results/result1.xlsx",
        "results/result2.xlsx",
        "results/result3.xlsx",
        "results/result4.xlsx",
    ],
}

(ROOT / "results" / "复现清单.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
