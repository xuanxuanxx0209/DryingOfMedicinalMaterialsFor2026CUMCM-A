#!/usr/bin/env python3
"""绘制问题二的原始数据、求解过程和最终结果候选图。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent
FIGURE_SCRIPTS = Path(r"C:\Users\23572\.codex\skills\math-modeling\tools\figure\scripts")
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(FIGURE_SCRIPTS))

from utils.plot_style import add_panel_labels, publication_subplots  # noqa: E402
from export_figure import export_figure  # noqa: E402
from setup_style import setup_style  # noqa: E402
from visual_qa import audit_layout, print_report, render_preview  # noqa: E402


FIGURES_DIR = PROJECT_ROOT / "figures"
QA_DIR = FIGURES_DIR / "_qa"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURE_SIZE = (6.3, 3.9)
COLORS = {
    "blue": "#0072B2",
    "orange": "#D55E00",
    "green": "#009E73",
    "sky": "#56B4E9",
    "purple": "#CC79A7",
    "gray": "#6B7280",
    "black": "#111827",
}


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict, pd.DataFrame]:
    boundary = pd.read_excel(PROJECT_ROOT / "problem A" / "附件" / "附件1.xlsx")
    boundary.columns = ["时间_s", "温度_C", "空气含湿量_kg_kg"]
    boundary = boundary.loc[boundary["时间_s"] <= 10800].copy()
    boundary["时间_h"] = boundary["时间_s"] / 3600.0
    boundary.to_csv(RESULTS_DIR / "问题2_空气边界.csv", index=False, encoding="utf-8-sig")

    temperature = pd.read_excel(RESULTS_DIR / "result2.xlsx", sheet_name="温度")
    moisture = pd.read_excel(RESULTS_DIR / "result2.xlsx", sheet_name="水分浓度")
    summary = json.loads((RESULTS_DIR / "问题2_结果摘要.json").read_text(encoding="utf-8"))
    iterations = pd.read_csv(RESULTS_DIR / "问题2_迭代次数.csv")
    return boundary, temperature, moisture, summary, iterations


def field_arrays(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    times = frame.iloc[:, 0].to_numpy(dtype=float)
    radii = np.asarray([float(value) for value in frame.columns[1:]], dtype=float)
    values = frame.iloc[:, 1:].to_numpy(dtype=float)
    return times / 3600.0, radii, values


def finish(fig, basename: str, size: tuple[float, float] = FIGURE_SIZE) -> None:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    preview = QA_DIR / f"{basename}_preview.png"
    render_preview(fig, str(preview), dpi=150)
    issues = audit_layout(fig)
    report = print_report(issues)
    print(f"[{basename}]\n{report}")
    failures = [message for severity, message in issues if severity == "FAIL"]
    if failures:
        raise RuntimeError(f"{basename} 版面检查未通过：{'；'.join(failures)}")
    export_figure(
        fig,
        str(FIGURES_DIR / basename),
        formats=("pdf", "svg", "png"),
        dpi=300,
        size_inches=size,
        grayscale_preview=True,
    )
    grayscale_path = FIGURES_DIR / f"{basename}_grayscale.png"
    if grayscale_path.exists():
        from PIL import Image

        with Image.open(grayscale_path) as source:
            grayscale_pixels = source.copy()
        grayscale_pixels.save(grayscale_path, dpi=(300, 300))
    plt.close(fig)


def plot_boundary_series(boundary: pd.DataFrame) -> None:
    fig, axes = publication_subplots(2, 1, width="report", aspect=0.66, squeeze=False)
    axes = axes.ravel()
    axes[0].plot(boundary["时间_h"], boundary["温度_C"], color=COLORS["orange"])
    axes[0].set_ylabel("烘房温度  摄氏度")
    axes[0].set_xlim(0, 3)
    axes[0].set_xticklabels([])
    axes[1].plot(boundary["时间_h"], boundary["空气含湿量_kg_kg"], color=COLORS["blue"], linestyle="--")
    axes[1].set_xlabel("时间  小时")
    axes[1].set_ylabel("空气水分浓度  千克每千克")
    axes[1].set_xlim(0, 3)
    axes[1].ticklabel_format(axis="y", style="plain", useOffset=False)
    add_panel_labels(axes)
    finish(fig, "raw_q2_boundary_series", (6.3, 4.2))


def plot_boundary_relation(boundary: pd.DataFrame) -> None:
    fig, ax = publication_subplots(width="report", aspect=0.66)
    ax.plot(
        boundary["温度_C"],
        boundary["空气含湿量_kg_kg"],
        color="#B8BDC7",
        linewidth=0.8,
        zorder=1,
    )
    scatter = ax.scatter(
        boundary["温度_C"],
        boundary["空气含湿量_kg_kg"],
        c=boundary["时间_h"],
        cmap="viridis",
        s=18,
        edgecolors="white",
        linewidths=0.25,
        zorder=2,
    )
    correlation = boundary[["温度_C", "空气含湿量_kg_kg"]].corr().iloc[0, 1]
    ax.text(0.04, 0.95, f"Pearson r = {correlation:.3f}", transform=ax.transAxes, va="top")
    ax.set_xlabel("烘房温度  摄氏度")
    ax.set_ylabel("空气含湿量  千克每千克")
    colorbar = fig.colorbar(scatter, ax=ax, pad=0.03)
    colorbar.set_label("时间  小时")
    finish(fig, "raw_q2_boundary_relation")


def plot_boundary_rates(boundary: pd.DataFrame) -> None:
    changes = boundary.diff().iloc[1:].copy()
    changes["时间_h"] = boundary["时间_h"].iloc[1:].to_numpy()
    fig, axes = publication_subplots(2, 1, width="report", aspect=0.66, squeeze=False)
    axes = axes.ravel()
    axes[0].plot(changes["时间_h"], changes["温度_C"], color=COLORS["orange"])
    axes[0].axhline(0, color=COLORS["gray"], linewidth=0.6, linestyle=":")
    axes[0].set_ylabel("每分钟温升  摄氏度")
    axes[0].set_xlim(0, 3)
    axes[0].set_xticklabels([])
    axes[1].plot(changes["时间_h"], changes["空气含湿量_kg_kg"], color=COLORS["blue"], linestyle="--")
    axes[1].axhline(0, color=COLORS["gray"], linewidth=0.6, linestyle=":")
    axes[1].set_xlabel("时间  小时")
    axes[1].set_ylabel("每分钟含湿量增量")
    axes[1].set_xlim(0, 3)
    axes[1].ticklabel_format(axis="y", style="sci", scilimits=(-3, 3))
    add_panel_labels(axes)
    finish(fig, "raw_q2_boundary_rates", (6.3, 4.2))


def plot_picard_iterations(iterations: pd.DataFrame) -> None:
    fig, axes = publication_subplots(1, 2, width="report", aspect=0.57, width_ratios=(2.15, 1.0), squeeze=False)
    axes = axes.ravel()
    data = iterations.loc[iterations["时间_s"] > 0].copy()
    axes[0].step(data["时间_s"] / 3600.0, data["Picard迭代次数"], where="post", color=COLORS["blue"])
    axes[0].set_xlabel("时间  小时")
    axes[0].set_ylabel("Picard 迭代次数")
    axes[0].set_xlim(0, 3)
    axes[0].set_ylim(2.35, 4.3)
    axes[0].set_yticks([3, 4])
    axes[0].text(
        0.02,
        0.04,
        r"阈值  $10^{-8}$ 摄氏度和 $10^{-10}$ 千克每千克，迭代上限 40 次",
        transform=axes[0].transAxes,
        fontsize=6.5,
    )

    counts = data["Picard迭代次数"].value_counts().sort_index()
    axes[1].plot(counts.to_numpy(), counts.index.to_numpy(), "o", color=COLORS["orange"], markersize=5)
    for y_value, x_value in zip(counts.index, counts.to_numpy()):
        axes[1].hlines(y_value, 0, x_value, color=COLORS["orange"], linewidth=1.0)
        axes[1].text(x_value, y_value + 0.08, f"{x_value}", ha="right", va="bottom", fontsize=7)
    axes[1].set_xlabel("时间层数")
    axes[1].set_ylabel("迭代次数")
    axes[1].set_yticks([3, 4])
    axes[1].set_xlim(0, max(counts) * 1.08)
    add_panel_labels(axes)
    finish(fig, "process_q2_picard_iterations", (6.3, 3.7))


def plot_refinement(summary: dict) -> None:
    verification = summary["verification"]
    labels = ["时间步减半", "空间网格减半"]
    temperature_error = [
        verification["max_temperature_difference_time_refined_c"],
        verification["max_temperature_difference_space_refined_c"],
    ]
    moisture_error = [
        verification["max_moisture_difference_time_refined_kg_per_kg"],
        verification["max_moisture_difference_space_refined_kg_per_kg"],
    ]
    fig, axes = publication_subplots(1, 2, width="report", aspect=0.57, squeeze=False)
    axes = axes.ravel()
    for axis, values, ylabel, color in (
        (axes[0], temperature_error, "温度最大绝对差  摄氏度", COLORS["orange"]),
        (axes[1], moisture_error, "含水率最大绝对差  千克每千克", COLORS["blue"]),
    ):
        x = np.arange(2)
        axis.plot(x, values, "o", color=color, markersize=5)
        axis.vlines(x, 1e-9, values, color=color, linewidth=1.0)
        axis.axhline(5e-5, color=COLORS["gray"], linestyle="--", linewidth=0.8)
        axis.text(
            0.97,
            0.92,
            "四位小数半单位",
            transform=axis.transAxes,
            ha="right",
            va="top",
            color=COLORS["gray"],
            fontsize=6.5,
        )
        axis.set_yscale("log")
        axis.set_xticks(x, labels)
        axis.tick_params(axis="x", rotation=12)
        axis.set_ylabel(ylabel)
        axis.set_ylim(1e-9, 1e-4)
    add_panel_labels(axes)
    finish(fig, "process_q2_refinement", (6.3, 3.7))


def plot_sensitivity(summary: dict) -> None:
    frame = pd.DataFrame(summary["sensitivity"])
    labels = [r"$h$  0.8 倍", r"$h$  1.2 倍", r"$h_m$  0.8 倍", r"$h_m$  1.2 倍"]
    y = np.arange(len(labels))
    colors = [COLORS["orange"], COLORS["orange"], COLORS["blue"], COLORS["blue"]]
    markers = ["o", "s", "o", "s"]
    fig, axes = publication_subplots(1, 2, width="report", aspect=0.57, squeeze=False)
    axes = axes.ravel()
    columns = ["max_temperature_change_c", "max_moisture_change_kg_per_kg"]
    xlabels = ["温度最大变化  摄氏度", "含水率最大变化  千克每千克"]
    for axis, column, xlabel in zip(axes, columns, xlabels):
        values = frame[column].to_numpy()
        for index, value in enumerate(values):
            axis.hlines(y[index], 0, value, color=colors[index], linewidth=1.0)
            axis.plot(value, y[index], marker=markers[index], color=colors[index], markersize=5)
        axis.set_yticks(y, labels)
        axis.set_xlabel(xlabel)
        axis.set_xlim(left=0)
        axis.invert_yaxis()
    add_panel_labels(axes)
    finish(fig, "process_q2_sensitivity", (6.3, 3.7))


def plot_field(time_h: np.ndarray, radii: np.ndarray, values: np.ndarray, basename: str, label: str, cmap: str) -> None:
    fig, ax = publication_subplots(width="report", aspect=0.60)
    display_stride = 30
    display_time = time_h[::display_stride]
    display_values = values[::display_stride]
    if display_time[-1] != time_h[-1]:
        display_time = np.append(display_time, time_h[-1])
        display_values = np.vstack([display_values, values[-1]])
    image = ax.pcolormesh(display_time, radii, display_values.T, shading="auto", cmap=cmap)
    ax.set_xlabel("时间  小时")
    ax.set_ylabel("到药材中心的距离  厘米")
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 2)
    colorbar = fig.colorbar(image, ax=ax, pad=0.03)
    colorbar.set_label(label)
    finish(fig, basename, (6.3, 3.8))


def plot_center_surface_gap(
    time_h: np.ndarray,
    temperature_values: np.ndarray,
    moisture_values: np.ndarray,
) -> None:
    temperature_gap = temperature_values[:, -1] - temperature_values[:, 0]
    moisture_gap = moisture_values[:, 0] - moisture_values[:, -1]
    report_times = np.asarray([1800, 3600, 5400, 7200, 9000, 10800], dtype=float)
    report_indices = np.searchsorted(time_h * 3600.0, report_times)
    fig, axes = publication_subplots(2, 1, width="report", aspect=0.66, squeeze=False)
    axes = axes.ravel()
    axes[0].plot(time_h, temperature_gap, color=COLORS["orange"])
    axes[0].plot(time_h[report_indices], temperature_gap[report_indices], "o", color=COLORS["black"], markersize=3)
    axes[0].set_ylabel("表面减中心温差  摄氏度")
    axes[0].set_xlim(0, 3)
    axes[0].set_ylim(bottom=0)
    axes[0].set_xticklabels([])
    axes[1].plot(time_h, moisture_gap, color=COLORS["blue"], linestyle="--")
    axes[1].plot(time_h[report_indices], moisture_gap[report_indices], "s", color=COLORS["black"], markersize=3)
    axes[1].set_xlabel("时间  小时")
    axes[1].set_ylabel("中心减表面含水率")
    axes[1].set_xlim(0, 3)
    axes[1].set_ylim(bottom=0)
    add_panel_labels(axes)
    finish(fig, "result_q2_center_surface_gap", (6.3, 4.2))


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    setup_style(journal="nature", lang="zh", use_sciplots=True, serif_for_zh=False)
    boundary, temperature, moisture, summary, iterations = load_data()
    time_h, radii, temperature_values = field_arrays(temperature)
    moisture_time_h, moisture_radii, moisture_values = field_arrays(moisture)
    if not np.array_equal(time_h, moisture_time_h) or not np.array_equal(radii, moisture_radii):
        raise ValueError("温度表和水分浓度表的网格不一致")

    plot_boundary_series(boundary)
    plot_boundary_relation(boundary)
    plot_boundary_rates(boundary)
    plot_picard_iterations(iterations)
    plot_refinement(summary)
    plot_sensitivity(summary)
    plot_field(time_h, radii, temperature_values, "result_q2_temperature_field", "温度  摄氏度", "inferno")
    plot_field(time_h, radii, moisture_values, "result_q2_moisture_field", "含水率  千克每千克", "cividis_r")
    plot_center_surface_gap(time_h, temperature_values, moisture_values)
    print("问题二九张候选图已完成")


if __name__ == "__main__":
    main()
