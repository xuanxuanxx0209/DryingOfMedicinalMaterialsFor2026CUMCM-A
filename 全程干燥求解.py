from __future__ import annotations

import argparse
import hashlib
import json
import platform
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import openpyxl

import 药材烘干求解 as core


PROJECT_ROOT = Path(__file__).resolve().parent
AIR_PATH = PROJECT_ROOT / "problem A" / "附件" / "附件1.xlsx"
RADIUS_PATH = PROJECT_ROOT / "problem A" / "附件" / "附件2.xlsx"
TEMPLATE_DIR = PROJECT_ROOT / "problem A" / "附件" / "附件3"
RESULTS_DIR = PROJECT_ROOT / "results"

HEAT_TRANSFER_COEFFICIENT = 25.0
MASS_TRANSFER_COEFFICIENT = 8.0e-7
INITIAL_TEMPERATURE_C = 28.0
INITIAL_MOISTURE = 2.55
DRYING_THRESHOLD = 0.15


@dataclass(frozen=True)
class RadiusHistory:
    time_s: np.ndarray
    radius_m: np.ndarray

    def at(self, time_s: float) -> float:
        return float(
            np.interp(
                time_s,
                self.time_s,
                self.radius_m,
                left=self.radius_m[0],
                right=self.radius_m[-1],
            )
        )


@dataclass
class VariableSimulation:
    time_s: np.ndarray
    radius_m: np.ndarray
    node_coordinate: np.ndarray
    temperature_c: np.ndarray
    moisture: np.ndarray
    max_coupling_iterations: int
    moisture_balance_relative_error: float
    dry_time_s: float | None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_radius_history(path: Path = RADIUS_PATH) -> RadiusHistory:
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    worksheet = workbook.active
    rows = list(worksheet.iter_rows(values_only=True))
    workbook.close()
    if len(rows) != 146:
        raise ValueError(f"附件2有效行数应为146，实际为{len(rows)}")
    if tuple(rows[0]) != ("时间", "半径"):
        raise ValueError(f"附件2表头异常: {tuple(rows[0])}")
    data = np.asarray(rows[1:], dtype=float)
    if data.shape != (145, 2):
        raise ValueError(f"附件2数据形状异常: {data.shape}")
    if data[0, 0] != 0 or data[-1, 0] != 259200:
        raise ValueError("附件2时间范围不是0至259200秒")
    if not np.allclose(np.diff(data[:, 0]), 1800.0):
        raise ValueError("附件2时间间隔不是1800秒")
    radius_m = data[:, 1] / 100.0
    if np.any(np.diff(radius_m) > 1.0e-12):
        raise ValueError("附件2半径存在增大记录")
    if not np.isclose(radius_m[0], 0.02) or not np.isclose(
        radius_m[-1], 0.01198
    ):
        raise ValueError("附件2首末半径异常")
    return RadiusHistory(data[:, 0], radius_m)


def q23_properties(
    moisture: np.ndarray, temperature_c: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    safe_moisture = np.maximum(moisture, 1.0e-8)
    temperature_k = temperature_c + 273.15
    density = 650.0 + 128.0 * safe_moisture
    heat_capacity = 1450.0 + 2736.0 * safe_moisture / (safe_moisture + 1.0)
    conductivity = 0.21 + 0.38 * safe_moisture / (safe_moisture + 1.0)
    diffusivity = (
        2.4e-3
        * np.exp(-0.45 / safe_moisture)
        * np.exp(-3850.0 / temperature_k)
    )
    return density, heat_capacity, conductivity, diffusivity


def q4_properties(
    moisture: np.ndarray, temperature_c: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    safe_moisture = np.maximum(moisture, 1.0e-8)
    temperature_k = temperature_c + 273.15
    density = 760.0 + 90.0 * safe_moisture
    heat_capacity = 1850.0 + 2150.0 * safe_moisture / (safe_moisture + 1.0)
    conductivity = 0.12 + 0.20 * safe_moisture / (safe_moisture + 1.0)
    diffusivity = (
        4.2e-4
        * np.exp(-0.30 / safe_moisture)
        * np.exp(-3850.0 / temperature_k)
    )
    return density, heat_capacity, conductivity, diffusivity


def simulate_variable_model(
    *,
    model: str,
    end_time_s: float,
    time_step_s: float,
    intervals: int,
    record_interval_s: float,
    stop_at_dryness: bool = False,
    coupling_temperature_tolerance: float = 1.0e-8,
    coupling_moisture_tolerance: float = 1.0e-10,
    coupling_max_iterations: int = 40,
) -> VariableSimulation:
    if model not in {"q23", "q4"}:
        raise ValueError("model必须为q23或q4")
    step_count_float = end_time_s / time_step_s
    step_count = int(round(step_count_float))
    if not np.isclose(step_count, step_count_float):
        raise ValueError("结束时刻必须是时间步长的整数倍")
    record_stride_float = record_interval_s / time_step_s
    record_stride = int(round(record_stride_float))
    if not np.isclose(record_stride, record_stride_float):
        raise ValueError("记录间隔必须是时间步长的整数倍")

    air = core.read_air_boundary()
    radius_history = read_radius_history() if model == "q4" else None
    property_function = q23_properties if model == "q23" else q4_properties
    node_coordinate = np.linspace(0.0, 1.0, intervals + 1)
    temperature = np.full(intervals + 1, INITIAL_TEMPERATURE_C, dtype=float)
    moisture = np.full(intervals + 1, INITIAL_MOISTURE, dtype=float)

    recorded_time = [0.0]
    initial_radius = 0.02
    recorded_radius = [initial_radius]
    recorded_temperature = [temperature.copy()]
    recorded_moisture = [moisture.copy()]
    normalized_weights = np.empty(intervals + 1, dtype=float)
    normalized_faces = np.empty(intervals + 2, dtype=float)
    normalized_faces[0] = 0.0
    normalized_faces[-1] = 1.0
    normalized_faces[1:-1] = 0.5 * (
        node_coordinate[:-1] + node_coordinate[1:]
    )
    normalized_weights[:] = (
        normalized_faces[1:] ** 2 - normalized_faces[:-1] ** 2
    )
    if not np.isclose(np.sum(normalized_weights), 1.0):
        raise RuntimeError("归一化控制体权重之和不等于1")

    initial_mean_moisture = float(np.dot(normalized_weights, moisture))
    accumulated_boundary_loss = 0.0
    max_iterations_used = 0
    dry_time_s: float | None = None

    for step in range(1, step_count + 1):
        current_time = step * time_step_s
        radius_m = (
            0.02 if radius_history is None else radius_history.at(current_time)
        )
        grid = core.make_grid(radius_m=radius_m, intervals=intervals)
        ambient_temperature, ambient_moisture = air.at(current_time)
        temperature_guess = temperature.copy()
        moisture_guess = moisture.copy()
        converged = False

        for iteration in range(1, coupling_max_iterations + 1):
            density, heat_capacity, conductivity, _ = property_function(
                moisture_guess, temperature_guess
            )
            lower_t, diagonal_t, upper_t, rhs_t = core.assemble_implicit_system(
                grid,
                temperature,
                density * heat_capacity,
                conductivity,
                time_step_s,
                HEAT_TRANSFER_COEFFICIENT,
                ambient_temperature,
            )
            temperature_new = core.solve_tridiagonal(
                lower_t, diagonal_t, upper_t, rhs_t
            )
            _, _, _, diffusivity = property_function(
                moisture_guess, temperature_new
            )
            lower_c, diagonal_c, upper_c, rhs_c = core.assemble_implicit_system(
                grid,
                moisture,
                np.ones(intervals + 1, dtype=float),
                diffusivity,
                time_step_s,
                MASS_TRANSFER_COEFFICIENT,
                ambient_moisture,
            )
            moisture_new = core.solve_tridiagonal(
                lower_c, diagonal_c, upper_c, rhs_c
            )
            temperature_error = float(
                np.max(np.abs(temperature_new - temperature_guess))
            )
            moisture_error = float(np.max(np.abs(moisture_new - moisture_guess)))
            temperature_guess = temperature_new
            moisture_guess = moisture_new
            if (
                temperature_error <= coupling_temperature_tolerance
                and moisture_error <= coupling_moisture_tolerance
            ):
                converged = True
                break
        if not converged:
            raise RuntimeError(
                f"{model}耦合迭代在t={current_time:g}秒未收敛，"
                f"温度误差{temperature_error:.3e}，含水率误差{moisture_error:.3e}"
            )

        temperature = temperature_guess
        moisture = moisture_guess
        max_iterations_used = max(max_iterations_used, iteration)
        accumulated_boundary_loss += (
            time_step_s
            * 2.0
            * MASS_TRANSFER_COEFFICIENT
            / radius_m
            * (moisture[-1] - ambient_moisture)
        )

        if step % record_stride == 0:
            recorded_time.append(current_time)
            recorded_radius.append(radius_m)
            recorded_temperature.append(temperature.copy())
            recorded_moisture.append(moisture.copy())

        if stop_at_dryness and float(np.max(moisture)) < DRYING_THRESHOLD:
            dry_time_s = current_time
            if recorded_time[-1] != current_time:
                recorded_time.append(current_time)
                recorded_radius.append(radius_m)
                recorded_temperature.append(temperature.copy())
                recorded_moisture.append(moisture.copy())
            break

    if stop_at_dryness and dry_time_s is None:
        raise RuntimeError(f"{model}在{end_time_s / 3600:g}小时内未达到干燥阈值")

    final_mean_moisture = float(np.dot(normalized_weights, moisture))
    balance_residual = (
        final_mean_moisture - initial_mean_moisture + accumulated_boundary_loss
    )
    relative_balance_error = abs(balance_residual) / max(
        abs(initial_mean_moisture - final_mean_moisture), 1.0e-30
    )
    return VariableSimulation(
        time_s=np.asarray(recorded_time, dtype=float),
        radius_m=np.asarray(recorded_radius, dtype=float),
        node_coordinate=node_coordinate,
        temperature_c=np.asarray(recorded_temperature, dtype=float),
        moisture=np.asarray(recorded_moisture, dtype=float),
        max_coupling_iterations=max_iterations_used,
        moisture_balance_relative_error=float(relative_balance_error),
        dry_time_s=dry_time_s,
    )


def interpolate_at_physical_radii(
    simulation: VariableSimulation,
    field: np.ndarray,
    row_index: int,
    radii_cm: list[float],
) -> np.ndarray:
    current_radius_cm = 100.0 * simulation.radius_m[row_index]
    physical_nodes_cm = simulation.node_coordinate * current_radius_cm
    return np.interp(radii_cm, physical_nodes_cm, field[row_index])


def write_result2(simulation: VariableSimulation, output_path: Path) -> None:
    if not np.allclose(np.diff(simulation.time_s), 1.0):
        raise ValueError("result2要求每1秒记录一次")
    template = openpyxl.load_workbook(TEMPLATE_DIR / "result2.xlsx")
    radii_cm = [round(0.1 * index, 1) for index in range(21)]
    for sheet_name, field in (
        ("温度", simulation.temperature_c),
        ("水分浓度", simulation.moisture),
    ):
        worksheet = template[sheet_name]
        if worksheet.max_row > 1:
            worksheet.delete_rows(2, worksheet.max_row - 1)
        worksheet.cell(1, 1, "时间\\到药材中心的距离")
        for column, radius_cm in enumerate(radii_cm, start=2):
            worksheet.cell(1, column, radius_cm)
        for row, time_s in enumerate(simulation.time_s[1:], start=2):
            source_index = row - 1
            values = interpolate_at_physical_radii(
                simulation, field, source_index, radii_cm
            )
            worksheet.cell(row, 1, int(round(float(time_s))))
            for column, value in enumerate(values, start=2):
                worksheet.cell(row, column, round(float(value), 4))
        worksheet.freeze_panes = "B2"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(".tmp.xlsx")
    template.save(temporary)
    template.close()
    temporary.replace(output_path)


def write_result3(simulation: VariableSimulation, output_path: Path) -> None:
    template = openpyxl.load_workbook(TEMPLATE_DIR / "result3.xlsx")
    worksheet = template.active
    if worksheet.max_row > 1:
        worksheet.delete_rows(2, worksheet.max_row - 1)
    radii_cm = [round(0.1 * index, 1) for index in range(21)]
    worksheet.cell(1, 1, "时间\\到药材中心的距离")
    for column, radius_cm in enumerate(radii_cm, start=2):
        worksheet.cell(1, column, radius_cm)
    for row, time_s in enumerate(simulation.time_s[1:], start=2):
        source_index = row - 1
        values = interpolate_at_physical_radii(
            simulation, simulation.moisture, source_index, radii_cm
        )
        worksheet.cell(row, 1, int(round(float(time_s))))
        for column, value in enumerate(values, start=2):
            worksheet.cell(row, column, round(float(value), 4))
    worksheet.freeze_panes = "B2"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(".tmp.xlsx")
    template.save(temporary)
    template.close()
    temporary.replace(output_path)


def write_result4(simulation: VariableSimulation, output_path: Path) -> None:
    template = openpyxl.load_workbook(TEMPLATE_DIR / "result4.xlsx")
    worksheet = template.active
    if worksheet.max_row > 1:
        worksheet.delete_rows(2, worksheet.max_row - 1)
    fixed_radii_cm = [round(0.1 * index, 1) for index in range(20)]
    worksheet.cell(1, 1, "时间\\到药材中心的距离")
    for column, radius_cm in enumerate(fixed_radii_cm, start=2):
        worksheet.cell(1, column, radius_cm)
    surface_column = len(fixed_radii_cm) + 2
    worksheet.cell(1, surface_column, "药材表面")

    for row, time_s in enumerate(simulation.time_s[1:], start=2):
        source_index = row - 1
        current_radius_cm = 100.0 * simulation.radius_m[source_index]
        physical_nodes_cm = simulation.node_coordinate * current_radius_cm
        worksheet.cell(row, 1, int(round(float(time_s))))
        for column, radius_cm in enumerate(fixed_radii_cm, start=2):
            if radius_cm < current_radius_cm - 1.0e-10:
                value = np.interp(
                    radius_cm,
                    physical_nodes_cm,
                    simulation.moisture[source_index],
                )
                worksheet.cell(row, column, round(float(value), 4))
            else:
                worksheet.cell(row, column, None)
        worksheet.cell(
            row,
            surface_column,
            round(float(simulation.moisture[source_index, -1]), 4),
        )
    worksheet.freeze_panes = "B2"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(".tmp.xlsx")
    template.save(temporary)
    template.close()
    temporary.replace(output_path)


def requested_table(
    simulation: VariableSimulation,
    field: np.ndarray,
    times_s: list[float],
    radii_cm: list[float],
) -> list[list[float]]:
    rows: list[list[float]] = []
    for time_s in times_s:
        index = int(np.argmin(np.abs(simulation.time_s - time_s)))
        if not np.isclose(simulation.time_s[index], time_s):
            raise ValueError(f"记录结果不含时刻{time_s}秒")
        rows.append(
            interpolate_at_physical_radii(
                simulation, field, index, radii_cm
            ).tolist()
        )
    return rows


def run_smoke() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    q2 = simulate_variable_model(
        model="q23",
        end_time_s=600.0,
        time_step_s=1.0,
        intervals=20,
        record_interval_s=60.0,
    )
    q4 = simulate_variable_model(
        model="q4",
        end_time_s=3600.0,
        time_step_s=10.0,
        intervals=20,
        record_interval_s=60.0,
    )
    q2_rho, q2_cp, q2_k, q2_d = q23_properties(
        q2.moisture[-1], q2.temperature_c[-1]
    )
    q4_rho, q4_cp, q4_k, q4_d = q4_properties(
        q4.moisture[-1], q4.temperature_c[-1]
    )
    report = {
        "mode": "P1_q2_q4_smoke",
        "inputs": {
            str(AIR_PATH.relative_to(PROJECT_ROOT)): sha256_file(AIR_PATH),
            str(RADIUS_PATH.relative_to(PROJECT_ROOT)): sha256_file(RADIUS_PATH),
        },
        "q2": {
            "time_step_s": 1.0,
            "radial_intervals": 20,
            "end_time_s": 600.0,
            "temperature_range_c": [
                float(np.min(q2.temperature_c)),
                float(np.max(q2.temperature_c)),
            ],
            "moisture_range_kg_per_kg": [
                float(np.min(q2.moisture)),
                float(np.max(q2.moisture)),
            ],
            "property_ranges": {
                "density_kg_per_m3": [float(q2_rho.min()), float(q2_rho.max())],
                "heat_capacity_j_per_kg_k": [float(q2_cp.min()), float(q2_cp.max())],
                "conductivity_w_per_m_k": [float(q2_k.min()), float(q2_k.max())],
                "diffusivity_m2_per_s": [float(q2_d.min()), float(q2_d.max())],
            },
            "max_coupling_iterations": q2.max_coupling_iterations,
            "moisture_balance_relative_error": q2.moisture_balance_relative_error,
        },
        "q4": {
            "time_step_s": 10.0,
            "radial_intervals": 20,
            "end_time_s": 3600.0,
            "radius_start_m": float(q4.radius_m[0]),
            "radius_end_m": float(q4.radius_m[-1]),
            "temperature_range_c": [
                float(np.min(q4.temperature_c)),
                float(np.max(q4.temperature_c)),
            ],
            "moisture_range_kg_per_kg": [
                float(np.min(q4.moisture)),
                float(np.max(q4.moisture)),
            ],
            "property_ranges": {
                "density_kg_per_m3": [float(q4_rho.min()), float(q4_rho.max())],
                "heat_capacity_j_per_kg_k": [float(q4_cp.min()), float(q4_cp.max())],
                "conductivity_w_per_m_k": [float(q4_k.min()), float(q4_k.max())],
                "diffusivity_m2_per_s": [float(q4_d.min()), float(q4_d.max())],
            },
            "max_coupling_iterations": q4.max_coupling_iterations,
            "moisture_balance_relative_error": q4.moisture_balance_relative_error,
        },
    }
    output = RESULTS_DIR / "P1_q2_q4_smoke.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


def run_q2() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    authoritative = simulate_variable_model(
        model="q23",
        end_time_s=10800.0,
        time_step_s=1.0,
        intervals=160,
        record_interval_s=1.0,
    )
    time_refined = simulate_variable_model(
        model="q23",
        end_time_s=10800.0,
        time_step_s=0.5,
        intervals=160,
        record_interval_s=1800.0,
    )
    space_refined = simulate_variable_model(
        model="q23",
        end_time_s=10800.0,
        time_step_s=1.0,
        intervals=320,
        record_interval_s=1800.0,
    )
    write_result2(authoritative, RESULTS_DIR / "result2.xlsx")

    times_s = [1800.0 * index for index in range(1, 7)]
    radii_cm = [0.0, 0.5, 1.0, 1.5, 2.0]
    temperature = np.asarray(
        requested_table(
            authoritative, authoritative.temperature_c, times_s, radii_cm
        )
    )
    moisture = np.asarray(
        requested_table(authoritative, authoritative.moisture, times_s, radii_cm)
    )
    time_temperature = np.asarray(
        requested_table(
            time_refined, time_refined.temperature_c, times_s, radii_cm
        )
    )
    time_moisture = np.asarray(
        requested_table(time_refined, time_refined.moisture, times_s, radii_cm)
    )
    space_temperature = np.asarray(
        requested_table(
            space_refined, space_refined.temperature_c, times_s, radii_cm
        )
    )
    space_moisture = np.asarray(
        requested_table(space_refined, space_refined.moisture, times_s, radii_cm)
    )
    summary = {
        "mode": "q2_full",
        "inputs": {
            str(AIR_PATH.relative_to(PROJECT_ROOT)): sha256_file(AIR_PATH)
        },
        "parameters": {
            "authoritative": {"intervals": 160, "time_step_s": 1.0},
            "time_refined": {"intervals": 160, "time_step_s": 0.5},
            "space_refined": {"intervals": 320, "time_step_s": 1.0},
        },
        "requested_times_s": times_s,
        "requested_radii_cm": radii_cm,
        "temperature_c": np.round(temperature, 8).tolist(),
        "moisture_kg_per_kg": np.round(moisture, 8).tolist(),
        "verification": {
            "max_temperature_difference_time_refined_c": float(
                np.max(np.abs(temperature - time_temperature))
            ),
            "max_moisture_difference_time_refined_kg_per_kg": float(
                np.max(np.abs(moisture - time_moisture))
            ),
            "max_temperature_difference_space_refined_c": float(
                np.max(np.abs(temperature - space_temperature))
            ),
            "max_moisture_difference_space_refined_kg_per_kg": float(
                np.max(np.abs(moisture - space_moisture))
            ),
            "moisture_balance_relative_error": authoritative.moisture_balance_relative_error,
            "max_coupling_iterations": authoritative.max_coupling_iterations,
        },
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "openpyxl": openpyxl.__version__,
            "platform": platform.platform(),
        },
    }
    (RESULTS_DIR / "问题2_结果摘要.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def run_q3() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    maximum_time_s = 7.0 * 24.0 * 3600.0
    authoritative = simulate_variable_model(
        model="q23",
        end_time_s=maximum_time_s,
        time_step_s=5.0,
        intervals=160,
        record_interval_s=60.0,
        stop_at_dryness=True,
    )
    time_coarse = simulate_variable_model(
        model="q23",
        end_time_s=maximum_time_s,
        time_step_s=10.0,
        intervals=160,
        record_interval_s=60.0,
        stop_at_dryness=True,
    )
    space_coarse = simulate_variable_model(
        model="q23",
        end_time_s=maximum_time_s,
        time_step_s=5.0,
        intervals=80,
        record_interval_s=60.0,
        stop_at_dryness=True,
    )
    write_result3(authoritative, RESULTS_DIR / "result3.xlsx")
    if authoritative.dry_time_s is None:
        raise RuntimeError("问题三未返回干燥时长")
    six_hour_times = list(
        np.arange(6.0 * 3600.0, authoritative.dry_time_s, 6.0 * 3600.0)
    )
    table_times = six_hour_times + [authoritative.dry_time_s]
    radii_cm = [0.0, 0.5, 1.0, 1.5, 2.0]
    table = requested_table(
        authoritative, authoritative.moisture, table_times, radii_cm
    )
    summary = {
        "mode": "q3_full",
        "dry_time_s": authoritative.dry_time_s,
        "dry_time_h": authoritative.dry_time_s / 3600.0,
        "table_times_s": table_times,
        "requested_radii_cm": radii_cm,
        "moisture_kg_per_kg": np.round(table, 8).tolist(),
        "verification": {
            "time_coarse_dry_time_s": time_coarse.dry_time_s,
            "space_coarse_dry_time_s": space_coarse.dry_time_s,
            "time_step_difference_s": float(
                abs(authoritative.dry_time_s - float(time_coarse.dry_time_s))
            ),
            "space_grid_difference_s": float(
                abs(authoritative.dry_time_s - float(space_coarse.dry_time_s))
            ),
            "moisture_balance_relative_error": authoritative.moisture_balance_relative_error,
            "max_coupling_iterations": authoritative.max_coupling_iterations,
        },
    }
    (RESULTS_DIR / "问题3_结果摘要.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def run_q4() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    maximum_time_s = 7.0 * 24.0 * 3600.0
    authoritative = simulate_variable_model(
        model="q4",
        end_time_s=maximum_time_s,
        time_step_s=5.0,
        intervals=160,
        record_interval_s=60.0,
        stop_at_dryness=True,
    )
    time_coarse = simulate_variable_model(
        model="q4",
        end_time_s=maximum_time_s,
        time_step_s=10.0,
        intervals=160,
        record_interval_s=60.0,
        stop_at_dryness=True,
    )
    space_coarse = simulate_variable_model(
        model="q4",
        end_time_s=maximum_time_s,
        time_step_s=5.0,
        intervals=80,
        record_interval_s=60.0,
        stop_at_dryness=True,
    )
    write_result4(authoritative, RESULTS_DIR / "result4.xlsx")
    if authoritative.dry_time_s is None:
        raise RuntimeError("问题四未返回干燥时长")
    six_hour_times = list(
        np.arange(6.0 * 3600.0, authoritative.dry_time_s, 6.0 * 3600.0)
    )
    table_times = six_hour_times + [authoritative.dry_time_s]
    summary_rows = []
    for time_s in table_times:
        index = int(np.argmin(np.abs(authoritative.time_s - time_s)))
        current_radius_cm = 100.0 * authoritative.radius_m[index]
        requested = [
            radius for radius in (0.0, 0.5, 1.0, 1.5) if radius < current_radius_cm
        ]
        values = interpolate_at_physical_radii(
            authoritative, authoritative.moisture, index, requested
        ).tolist()
        summary_rows.append(
            {
                "time_s": time_s,
                "radius_cm": current_radius_cm,
                "fixed_radii_cm": requested,
                "fixed_values": values,
                "surface_value": float(authoritative.moisture[index, -1]),
            }
        )
    summary = {
        "mode": "q4_full",
        "inputs": {
            str(AIR_PATH.relative_to(PROJECT_ROOT)): sha256_file(AIR_PATH),
            str(RADIUS_PATH.relative_to(PROJECT_ROOT)): sha256_file(RADIUS_PATH),
        },
        "dry_time_s": authoritative.dry_time_s,
        "dry_time_h": authoritative.dry_time_s / 3600.0,
        "table": summary_rows,
        "verification": {
            "time_coarse_dry_time_s": time_coarse.dry_time_s,
            "space_coarse_dry_time_s": space_coarse.dry_time_s,
            "time_step_difference_s": float(
                abs(authoritative.dry_time_s - float(time_coarse.dry_time_s))
            ),
            "space_grid_difference_s": float(
                abs(authoritative.dry_time_s - float(space_coarse.dry_time_s))
            ),
            "moisture_balance_relative_error": authoritative.moisture_balance_relative_error,
            "max_coupling_iterations": authoritative.max_coupling_iterations,
        },
    }
    (RESULTS_DIR / "问题4_结果摘要.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="2026 CUMCM A题全程干燥求解")
    parser.add_argument(
        "--mode",
        choices=("smoke", "q2", "q3", "q4", "all"),
        default="smoke",
    )
    arguments = parser.parse_args()
    if arguments.mode == "smoke":
        run_smoke()
    elif arguments.mode == "q2":
        run_q2()
    elif arguments.mode == "q3":
        run_q3()
    elif arguments.mode == "q4":
        run_q4()
    else:
        run_q2()
        run_q3()
        run_q4()


if __name__ == "__main__":
    main()
