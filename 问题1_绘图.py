from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
SKILL_ROOT = Path(r"C:\Users\23572\.codex\skills\math-modeling")
FIGURE_TOOLS = SKILL_ROOT / "tools" / "figure" / "scripts"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(FIGURE_TOOLS))

from export_figure import export_figure
from setup_style import setup_style
from utils.plot_style import PALETTE, add_panel_labels, audit_design, audit_layout


FIGURES_DIR = PROJECT_ROOT / "figures"
AIR_PATH = PROJECT_ROOT / "problem A" / "附件" / "附件1.xlsx"
RESULT1_PATH = PROJECT_ROOT / "results" / "result1.xlsx"
CONVERGENCE_PATH = PROJECT_ROOT / "results" / "问题1_网格收敛.csv"


def ensure_figure_is_valid(figure: plt.Figure) -> None:
    issues = audit_layout(figure) + audit_design(figure)
    if issues:
        raise ValueError("图形预检未通过: " + "；".join(issues))


def export(figure: plt.Figure, basename: str, size: tuple[float, float]) -> None:
    ensure_figure_is_valid(figure)
    export_figure(
        figure,
        str(FIGURES_DIR / basename),
        formats=("pdf", "svg", "png"),
        size_inches=size,
        dpi=300,
        grayscale_preview=True,
        pad_inches=0.04,
    )
    plt.close(figure)


def plot_raw_boundary() -> None:
    air = pd.read_excel(AIR_PATH, sheet_name=0, header=0)
    if tuple(air.columns) != ("时间", "温度", "水分浓度"):
        raise ValueError(f"附件1表头异常: {tuple(air.columns)}")
    air = air.loc[air["时间"] <= 1800].copy()
    if len(air) != 31 or air.isna().any().any():
        raise ValueError("问题一边界记录数量或缺失值异常")
    time_min = air["时间"].to_numpy(dtype=float) / 60.0

    figure, axes = plt.subplots(1, 2, figsize=(6.3, 2.45), layout="constrained")
    axes[0].plot(
        time_min,
        air["温度"],
        color=PALETTE["primary"],
        marker="o",
        markevery=5,
        markerfacecolor="white",
        markeredgewidth=0.7,
    )
    axes[0].set_xlabel("时间 / min")
    axes[0].set_ylabel("温度 / ℃")
    axes[0].set_title("烘房温度")
    axes[0].set_xlim(0, 30)

    axes[1].plot(
        time_min,
        air["水分浓度"],
        color=PALETTE["contrast"],
        linestyle="--",
        marker="s",
        markevery=5,
        markerfacecolor="white",
        markeredgewidth=0.7,
    )
    axes[1].set_xlabel("时间 / min")
    axes[1].set_ylabel("水分浓度 / kg·kg$^{-1}$")
    axes[1].set_title("空气水分浓度")
    axes[1].set_xlim(0, 30)
    add_panel_labels(axes)
    export(figure, "raw_q1_air_boundary", (6.3, 2.45))


def plot_convergence() -> None:
    data = pd.read_csv(CONVERGENCE_PATH)
    expected = {"时间步减半", "空间步减半"}
    if set(data["检验"]) != expected or len(data) != 4:
        raise ValueError("问题一收敛结果结构异常")
    order = ["时间步减半", "空间步减半"]
    colors = [PALETTE["primary"], PALETTE["contrast"]]
    figure, axes = plt.subplots(1, 2, figsize=(6.3, 2.4), layout="constrained")
    for axis, variable, title, unit in (
        (axes[0], "温度_C", "温度离散误差", "最大绝对差 / ℃"),
        (
            axes[1],
            "水分浓度_kg_per_kg",
            "含水率离散误差",
            "最大绝对差 / kg·kg$^{-1}$",
        ),
    ):
        subset = data.loc[data["变量"] == variable].set_index("检验").loc[order]
        values = subset["最大绝对差"].to_numpy(dtype=float)
        y = np.arange(2)
        for index, value in enumerate(values):
            axis.hlines(y[index], 0.0, value, color=colors[index], linewidth=1.2)
            axis.plot(
                value,
                y[index],
                marker="o" if index == 0 else "s",
                color=colors[index],
                markerfacecolor="white",
                markeredgewidth=0.9,
            )
            axis.text(value, y[index] + 0.14, f"{value:.2g}", ha="center", va="bottom")
        axis.set_yticks(y, order)
        axis.set_ylim(-0.55, 1.55)
        axis.set_xlim(left=0)
        axis.set_xlabel(unit)
        axis.set_title(title)
    add_panel_labels(axes)
    export(figure, "process_q1_convergence", (6.3, 2.4))


def plot_result_fields() -> None:
    temperature = pd.read_excel(RESULT1_PATH, sheet_name="温度", header=0)
    moisture = pd.read_excel(RESULT1_PATH, sheet_name="水分浓度", header=0)
    if temperature.shape != (1800, 22) or moisture.shape != (1800, 22):
        raise ValueError("result1工作表行列数异常")
    if temperature.isna().any().any() or moisture.isna().any().any():
        raise ValueError("result1含有缺失值")
    time_min = temperature.iloc[:, 0].to_numpy(dtype=float) / 60.0
    radius_cm = np.asarray(temperature.columns[1:], dtype=float)
    temperature_field = temperature.iloc[:, 1:].to_numpy(dtype=float)
    moisture_field = moisture.iloc[:, 1:].to_numpy(dtype=float)

    figure, axes = plt.subplots(1, 2, figsize=(6.3, 2.55), layout="constrained")
    meshes = []
    for axis, field, title, color_map, color_label in (
        (axes[0], temperature_field, "药材温度场", "magma", "温度 / ℃"),
        (
            axes[1],
            moisture_field,
            "药材含水率场",
            "viridis",
            "含水率 / kg·kg$^{-1}$",
        ),
    ):
        mesh = axis.pcolormesh(
            radius_cm,
            time_min,
            field,
            shading="auto",
            cmap=color_map,
        )
        meshes.append(mesh)
        axis.set_xlabel("距轴线距离 / cm")
        axis.set_ylabel("时间 / min")
        axis.set_title(title)
        axis.set_xlim(0, 2)
        axis.set_ylim(0, 30)
        colorbar = figure.colorbar(mesh, ax=axis, pad=0.02)
        colorbar.set_label(color_label)
    add_panel_labels(axes)
    export(figure, "result_q1_fields", (6.3, 2.55))


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    style = setup_style(
        journal="general",
        lang="zh",
        serif_for_zh=True,
        use_sciplots=False,
        constrained_layout=True,
    )
    print(f"使用字体: {style['cjk_font']}")
    plot_raw_boundary()
    plot_convergence()
    plot_result_fields()


if __name__ == "__main__":
    main()
