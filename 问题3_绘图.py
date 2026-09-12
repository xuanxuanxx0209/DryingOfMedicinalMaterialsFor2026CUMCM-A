#!/usr/bin/env python3
"""绘制问题三的原始数据、求解过程和最终结果候选图。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
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
COLORS = {
    "blue": "#0072B2",
    "orange": "#D55E00",
    "green": "#009E73",
    "sky": "#56B4E9",
    "purple": "#CC79A7",
    "gray": "#6B7280",
    "black": "#111827",
}


def load_data():
    boundary = pd.read_excel(PROJECT_ROOT / "problem A" / "附件" / "附件1.xlsx")
    boundary.columns = ["时间_s", "温度_C", "空气含湿量_kg_kg"]
    boundary["时间_h"] = boundary["时间_s"] / 3600.0
    stable = boundary.loc[boundary["时间_s"] >= 9000].copy()

    process = pd.read_csv(RESULTS_DIR / "问题3_关键过程.csv")
    process.columns = [
        "时间_s", "时间_h", "含水率_0_cm", "含水率_0.5_cm", "含水率_1_cm",
        "含水率_1.5_cm", "含水率_2_cm", "最大含水率", "最大值半径_cm",
    ]
    time_refinement = pd.read_csv(RESULTS_DIR / "问题3_时间步敏感性.csv")
    time_refinement.columns = ["时间步_s", "烘干时长_s", "烘干时长_h", "相对参考差_s"]
    space_refinement = pd.read_csv(RESULTS_DIR / "问题3_空间网格敏感性.csv")
    space_refinement.columns = ["径向区间数", "时间步_s", "烘干时长_s", "烘干时长_h"]
    sensitivity = pd.read_csv(RESULTS_DIR / "问题3_边界敏感性.csv")
    sensitivity.columns = [
        "工况", "温度_C", "空气含湿量_kg_kg", "换热系数", "传质系数",
        "烘干时长_s", "烘干时长_h", "相对变化",
    ]
    iterations = pd.read_csv(RESULTS_DIR / "问题3_迭代次数.csv")
    iterations.columns = ["时间_s", "迭代次数"]
    summary = json.loads((RESULTS_DIR / "问题3_结果摘要.json").read_text(encoding="utf-8"))

    field = pd.read_excel(RESULTS_DIR / "result3.xlsx")
    field_time = field.iloc[:, 0].to_numpy(dtype=float)
    field_radii = np.asarray([float(item) for item in field.columns[1:]], dtype=float)
    field_values = field.iloc[:, 1:].to_numpy(dtype=float)
    field_time = np.insert(field_time, 0, 0.0)
    field_values = np.vstack([np.full(field_radii.size, 2.55), field_values])
    return (
        boundary, stable, process, time_refinement, space_refinement,
        sensitivity, iterations, summary, field_time, field_radii, field_values,
    )


def finish(fig, basename: str, size=(6.3, 3.9)) -> None:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    render_preview(fig, str(QA_DIR / f"{basename}_preview.png"), dpi=150)
    issues = audit_layout(fig)
    print(f"[{basename}]\n{print_report(issues)}")
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
            gray = source.copy()
        gray.save(grayscale_path, dpi=(300, 300))
    plt.close(fig)


def plot_air_full(boundary: pd.DataFrame) -> None:
    fig, axes = publication_subplots(2, 1, width="report", aspect=0.66, squeeze=False)
    axes = axes.ravel()
    for axis in axes:
        axis.axvspan(2.5, 4.0, color="#D9DEE7", alpha=0.55, linewidth=0)
        axis.axvline(2.5, color=COLORS["gray"], linestyle=":", linewidth=0.8)
        axis.set_xlim(0, 4)
    axes[0].plot(boundary["时间_h"], boundary["温度_C"], color=COLORS["orange"])
    axes[0].set_ylabel("烘房温度  摄氏度")
    axes[0].tick_params(labelbottom=False)
    axes[0].text(2.55, 29.3, "稳定段", color=COLORS["gray"], fontsize=7)
    axes[1].plot(
        boundary["时间_h"], boundary["空气含湿量_kg_kg"],
        color=COLORS["blue"], linestyle="--",
    )
    axes[1].set_xlabel("时间  小时")
    axes[1].set_ylabel("空气水分浓度  千克每千克")
    axes[1].ticklabel_format(axis="y", style="plain", useOffset=False)
    add_panel_labels(axes)
    finish(fig, "raw_q3_air_full", (6.3, 4.2))


def plot_air_stable(stable: pd.DataFrame, summary: dict) -> None:
    stats = summary["stable_air"]
    fig, axes = publication_subplots(1, 2, width="report", aspect=0.56, squeeze=False)
    axes = axes.ravel()
    specs = (
        ("温度_C", stats["temperature_mean_c"], stats["temperature_std_c"],
         COLORS["orange"], "烘房温度  摄氏度"),
        ("空气含湿量_kg_kg", stats["moisture_mean_kg_per_kg"],
         stats["moisture_std_kg_per_kg"], COLORS["blue"], "空气水分浓度  千克每千克"),
    )
    for axis, (column, mean, sd, color, ylabel) in zip(axes, specs):
        axis.plot(stable["时间_h"], stable[column], color=color, linewidth=0.9)
        axis.axhline(mean, color=COLORS["black"], linestyle="--", linewidth=0.8, label="稳定段均值")
        axis.fill_between(
            stable["时间_h"], mean - sd, mean + sd,
            color=color, alpha=0.15, linewidth=0, label="总体标准差范围",
        )
        axis.set_xlabel("时间  小时")
        axis.set_ylabel(ylabel)
        axis.set_xlim(2.5, 4.0)
        axis.ticklabel_format(axis="y", style="plain", useOffset=False)
    axes[1].legend(loc="lower right", frameon=False)
    add_panel_labels(axes)
    finish(fig, "raw_q3_air_stable", (6.3, 3.55))


def plot_air_distribution(stable: pd.DataFrame) -> None:
    fig, axes = publication_subplots(
        1, 3, width="report", aspect=0.48, width_ratios=(1.0, 1.0, 1.3), squeeze=False,
    )
    axes = axes.ravel()
    axes[0].hist(stable["温度_C"], bins=11, color=COLORS["orange"], alpha=0.72,
                 edgecolor="white", linewidth=0.4)
    axes[0].axvline(stable["温度_C"].mean(), color=COLORS["black"], linestyle="--", linewidth=0.8)
    axes[0].set_xlabel("烘房温度  摄氏度")
    axes[0].set_ylabel("记录数")
    axes[1].hist(stable["空气含湿量_kg_kg"], bins=11, color=COLORS["blue"], alpha=0.72,
                 edgecolor="white", linewidth=0.4)
    axes[1].axvline(stable["空气含湿量_kg_kg"].mean(), color=COLORS["black"], linestyle="--", linewidth=0.8)
    axes[1].set_xlabel("空气水分浓度  千克每千克")
    axes[1].set_ylabel("记录数")
    axes[1].ticklabel_format(axis="x", style="plain", useOffset=False)
    scatter = axes[2].scatter(
        stable["温度_C"], stable["空气含湿量_kg_kg"], c=stable["时间_h"],
        cmap="viridis", s=18, edgecolors="white", linewidths=0.25,
    )
    correlation = stable[["温度_C", "空气含湿量_kg_kg"]].corr().iloc[0, 1]
    axes[2].set_title(f"Pearson r = {correlation:.3f}", loc="left", pad=4)
    axes[2].set_xlabel("烘房温度  摄氏度")
    axes[2].set_ylabel("空气水分浓度  千克每千克")
    axes[2].ticklabel_format(axis="y", style="plain", useOffset=False)
    colorbar = fig.colorbar(scatter, ax=axes[2], pad=0.03)
    colorbar.set_label("时间  小时")
    add_panel_labels(axes)
    finish(fig, "raw_q3_air_distribution", (6.3, 3.2))


def plot_time_convergence(frame: pd.DataFrame) -> None:
    frame = frame.sort_values("时间步_s")
    fig, axes = publication_subplots(1, 2, width="report", aspect=0.56, squeeze=False)
    axes = axes.ravel()
    axes[0].plot(frame["时间步_s"], frame["烘干时长_s"], "o-", color=COLORS["blue"], markersize=4)
    axes[0].set_xlabel("时间步  秒")
    axes[0].set_ylabel("烘干时长  秒")
    axes[0].ticklabel_format(axis="y", style="plain", useOffset=False)
    axes[0].set_xticks([0.25, 0.5, 1.0])
    axes[1].plot(frame["时间步_s"], frame["相对参考差_s"], "o", color=COLORS["orange"], markersize=5)
    axes[1].hlines(1.0, 0.2, 1.05, color=COLORS["gray"], linestyle="--", linewidth=0.8)
    axes[1].text(1.02, 1.02, "1 秒门槛", ha="right", va="bottom", color=COLORS["gray"], fontsize=6.5)
    axes[1].set_xlabel("时间步  秒")
    axes[1].set_ylabel("相对 0.25 秒结果的绝对差  秒")
    axes[1].set_xlim(0.2, 1.05)
    axes[1].set_ylim(-0.05, 1.18)
    axes[1].set_xticks([0.25, 0.5, 1.0])
    add_panel_labels(axes)
    finish(fig, "process_q3_time_convergence", (6.3, 3.55))


def plot_space_convergence(frame: pd.DataFrame, summary: dict) -> None:
    verification = summary["verification"]
    fig, axes = publication_subplots(
        1, 2, width="report", aspect=0.56, width_ratios=(1.0, 1.35), squeeze=False,
    )
    axes = axes.ravel()
    axes[0].plot(frame["径向区间数"], frame["烘干时长_h"], "o-", color=COLORS["blue"], markersize=5)
    axes[0].set_xlabel("径向区间数")
    axes[0].set_ylabel("烘干时长  小时")
    axes[0].set_xticks([160, 320])
    ratios = np.asarray([
        verification["space_time_relative_difference"] / 0.001,
        verification["space_table_max_absolute_difference_kg_per_kg"] / 5e-5,
    ])
    labels = ["时长误差", "表值误差"]
    y = np.arange(2)
    axes[1].axvline(1.0, color=COLORS["gray"], linestyle="--", linewidth=0.8)
    axes[1].plot(ratios, y, "o", color=COLORS["orange"], markersize=5)
    axes[1].hlines(y, 0, ratios, color=COLORS["orange"], linewidth=1.0)
    axes[1].set_yticks(y, labels)
    axes[1].set_xlabel("误差与门槛之比")
    axes[1].set_xlim(0, max(2.25, ratios.max() * 1.12))
    axes[1].invert_yaxis()
    axes[1].text(1.02, 0.96, "门槛", transform=axes[1].get_xaxis_transform(), color=COLORS["gray"], fontsize=6.5)
    add_panel_labels(axes)
    finish(fig, "process_q3_space_convergence", (6.3, 3.55))


def plot_iterations(frame: pd.DataFrame) -> None:
    data = frame.loc[frame["时间_s"] > 0].copy()
    fig, axes = publication_subplots(
        1, 2, width="report", aspect=0.56, width_ratios=(2.2, 1.0), squeeze=False,
    )
    axes = axes.ravel()
    axes[0].step(data["时间_s"] / 3600.0, data["迭代次数"], where="post", color=COLORS["blue"])
    axes[0].set_xlabel("时间  小时")
    axes[0].set_ylabel("Picard 迭代次数")
    axes[0].set_xlim(0, data["时间_s"].max() / 3600.0)
    axes[0].set_ylim(2.35, 4.3)
    axes[0].set_yticks([3, 4])
    axes[0].text(0.02, 0.05, "温度阈值 1e-8  含水率阈值 1e-10  上限 40 次",
                 transform=axes[0].transAxes, fontsize=6.5)
    counts = data["迭代次数"].value_counts().sort_index()
    axes[1].hlines(counts.index, 0, counts.to_numpy(), color=COLORS["orange"], linewidth=1.0)
    axes[1].plot(counts.to_numpy(), counts.index, "o", color=COLORS["orange"], markersize=5)
    axes[1].set_xlabel("时间层数")
    axes[1].set_ylabel("迭代次数")
    axes[1].set_yticks([3, 4])
    axes[1].set_xlim(0, counts.max() * 1.08)
    add_panel_labels(axes)
    finish(fig, "process_q3_picard_iterations", (6.3, 3.55))


def plot_sensitivity(frame: pd.DataFrame) -> None:
    labels = ["稳定温度减一倍标准差", "稳定温度加一倍标准差", "空气水分减一倍标准差",
              "空气水分加一倍标准差", "附件末条记录", "端面通量上界"]
    values = 100.0 * frame["相对变化"].to_numpy()
    y = np.arange(len(labels))
    fig, ax = publication_subplots(width="report", aspect=0.60)
    ax.axvline(0, color=COLORS["black"], linewidth=0.7)
    ax.axvline(-1, color=COLORS["gray"], linestyle=":", linewidth=0.7)
    ax.axvline(1, color=COLORS["gray"], linestyle=":", linewidth=0.7)
    colors = [COLORS["orange"]] * 2 + [COLORS["blue"]] * 2 + [COLORS["purple"], COLORS["green"]]
    markers = ["o", "s", "o", "s", "D", "^"]
    for index, value in enumerate(values):
        ax.hlines(y[index], 0, value, color=colors[index], linewidth=1.0)
        ax.plot(value, y[index], marker=markers[index], color=colors[index], markersize=5)
    ax.set_yticks(y, labels)
    ax.set_xlabel("烘干时长相对基准变化  百分比")
    ax.set_xlim(-1.05, 1.05)
    ax.invert_yaxis()
    finish(fig, "process_q3_boundary_sensitivity", (6.3, 3.8))


def plot_threshold(process: pd.DataFrame, summary: dict) -> None:
    dry_h = summary["dry_time_h"]
    fig, axes = publication_subplots(
        1, 2, width="report", aspect=0.56, width_ratios=(1.55, 1.0), squeeze=False,
    )
    axes = axes.ravel()
    axes[0].plot(process["时间_h"], process["最大含水率"], color=COLORS["blue"])
    axes[0].axhline(0.15, color=COLORS["orange"], linestyle="--", linewidth=0.9)
    axes[0].axvline(dry_h, color=COLORS["gray"], linestyle=":", linewidth=0.8)
    axes[0].set_xlabel("时间  小时")
    axes[0].set_ylabel("最大含水率  千克每千克")
    axes[0].set_xlim(0, dry_h + 0.5)
    axes[0].set_ylim(0, 2.65)
    local = process.loc[process["时间_h"] >= dry_h - 6.0]
    axes[1].plot(local["时间_h"], local["最大含水率"], color=COLORS["blue"])
    axes[1].axhline(0.15, color=COLORS["orange"], linestyle="--", linewidth=0.9, label="判定阈值")
    axes[1].plot(dry_h, summary["moisture_kg_per_kg"][-1][0], "o", color=COLORS["black"], markersize=4)
    axes[1].text(dry_h - 0.2, 0.15055, f"终点  {dry_h:.4f} 小时", ha="right", va="bottom", fontsize=6.8)
    axes[1].set_xlabel("时间  小时")
    axes[1].set_ylabel("最大含水率  千克每千克")
    axes[1].set_xlim(dry_h - 6.0, dry_h + 0.15)
    axes[1].set_ylim(0.1485, 0.166)
    axes[1].legend(loc="upper right", frameon=False)
    add_panel_labels(axes)
    finish(fig, "result_q3_threshold", (6.3, 3.55))


def plot_profiles(process: pd.DataFrame) -> None:
    columns = ["含水率_0_cm", "含水率_0.5_cm", "含水率_1_cm", "含水率_1.5_cm", "含水率_2_cm"]
    labels = ["0 厘米", "0.5 厘米", "1.0 厘米", "1.5 厘米", "2.0 厘米"]
    colors = [COLORS["blue"], COLORS["sky"], COLORS["green"], COLORS["orange"], COLORS["purple"]]
    styles = ["-", "--", "-.", ":", (0, (5, 2))]
    markers = ["o", "s", "^", "D", "v"]
    fig, ax = publication_subplots(width="report", aspect=0.60)
    for column, label, color, style, marker in zip(columns, labels, colors, styles, markers):
        ax.plot(process["时间_h"], process[column], color=color, linestyle=style,
                marker=marker, markevery=430, markersize=3, label=label)
    ax.axhline(0.15, color=COLORS["black"], linestyle="--", linewidth=0.8, label="判定阈值")
    ax.set_xlabel("时间  小时")
    ax.set_ylabel("含水率  千克每千克")
    ax.set_xlim(0, process["时间_h"].max())
    ax.set_ylim(0, 2.65)
    ax.legend(ncol=3, loc="upper right", frameon=False)
    finish(fig, "result_q3_profiles", (6.3, 3.8))


def plot_field(time_s: np.ndarray, radii: np.ndarray, values: np.ndarray) -> None:
    stride = 10
    display_time = time_s[::stride]
    display_values = values[::stride]
    if display_time[-1] != time_s[-1]:
        display_time = np.append(display_time, time_s[-1])
        display_values = np.vstack([display_values, values[-1]])
    fig, ax = publication_subplots(width="report", aspect=0.60)
    image = ax.pcolormesh(display_time / 3600.0, radii, display_values.T, shading="auto", cmap="cividis_r")
    contour = ax.contour(display_time / 3600.0, radii, display_values.T, levels=[0.15],
                         colors=[COLORS["orange"]], linewidths=0.9)
    if contour.allsegs[0]:
        ax.clabel(contour, fmt={0.15: "0.15"}, inline=True, fontsize=6.5)
    ax.set_xlabel("时间  小时")
    ax.set_ylabel("到药材中心的距离  厘米")
    ax.set_xlim(0, time_s[-1] / 3600.0)
    ax.set_ylim(0, 2)
    colorbar = fig.colorbar(image, ax=ax, pad=0.03)
    colorbar.set_label("含水率  千克每千克")
    finish(fig, "result_q3_moisture_field", (6.3, 3.8))


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    setup_style(journal="nature", lang="zh", use_sciplots=True, serif_for_zh=False)
    data = load_data()
    (
        boundary, stable, process, time_refinement, space_refinement,
        sensitivity, iterations, summary, field_time, field_radii, field_values,
    ) = data
    plot_air_full(boundary)
    plot_air_stable(stable, summary)
    plot_air_distribution(stable)
    plot_time_convergence(time_refinement)
    plot_space_convergence(space_refinement, summary)
    plot_iterations(iterations)
    plot_sensitivity(sensitivity)
    plot_threshold(process, summary)
    plot_profiles(process)
    plot_field(field_time, field_radii, field_values)
    print("问题三十张候选图已完成")


if __name__ == "__main__":
    main()
