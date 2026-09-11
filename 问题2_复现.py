#!/usr/bin/env python3
"""用一条命令重建问题二的数值结果和全部候选图。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def run(script: str, *arguments: str) -> None:
    command = [sys.executable, "-X", "utf8", script, *arguments]
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    run("全程干燥求解.py", "--mode", "q2")
    run("问题2_绘图.py")
    print("问题二数值结果、result2.xlsx 和九张候选图已重建")


if __name__ == "__main__":
    main()
