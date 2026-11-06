"""Run the HBEDB subject-level analysis from local WFDB files."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from hbedb_sway import __version__
from hbedb_sway.constants import (
    ALL_OUTCOMES,
    BOOTSTRAP_REPLICATES,
    DATASET_DOI,
    DATASET_VERSION,
    LICENSE_SHORT,
    PERMUTATION_REPLICATES,
    PRIMARY_CONTRAST,
    PRIMARY_OUTCOME,
    RNG_SEED,
)
from hbedb_sway.design import (
    assert_export_frame,
    complete_subjects,
    contrast_frame,
    load_metadata,
    protocol_gap_summary,
    sample_description,
    scale_by_foot_length,
    subject_condition_means,
)
from hbedb_sway.inference import (
    age_slopes,
    condition_cell_means,
    factorial_contrast_table,
    fit_factorial,
    fit_log_age_model,
    random_intercept_icc,
    repetition_coefficient,
    repetition_reliability,
    summarize_age_differences,
    summarize_contrasts,
)
from hbedb_sway.io_wfdb import read_recording
from hbedb_sway.plots import (
    plot_age_distribution,
    plot_age_forest,
    plot_axis_forest,
    plot_condition_means,
    plot_condition_means_by_age,
    plot_contrast_distribution,
    plot_forest,
    plot_interaction_against_age,
    plot_quality,
    plot_stabilograms,
)
from hbedb_sway.qc import metrics_from_physical, quality_flags
from hbedb_sway.report import write_results

TRIAL_COLUMNS = [
    "trial",
    "subject",
    "vision",
    "surface",
    "age_years",
    "age_group",
    "sex",
    "height_cm",
    "weight_kg",
    "bmi",
    "foot_len_cm",
    "self_reported_disability",
    "rep_index",
    "n_samples",
    "fs_hz",
    "fz_mean_n",
    "fz_min_n",
    "fz_ratio",
    "cop_recon_cm",
    "max_step_cm",
    "range_ap_cm",
    "range_ml_cm",
    "mv_cm_s",
    "mv_ap_cm_s",
    "mv_ml_cm_s",
    "ellipse_cm2",
    "checksum_ok",
    "initial_ok",
    "header_age_mismatch",
    "header_height_mismatch",
    "header_weight_mismatch",
    "exclude",
    "exclude_reasons",
]


@dataclass
class AnalysisResult:
    trials: pd.DataFrame
    means: pd.DataFrame
    contrasts: pd.DataFrame
    contrast_summary: pd.DataFrame
    age_summary: pd.DataFrame
    age_slopes: pd.DataFrame
    descriptive: pd.DataFrame
    sample: pd.DataFrame
    reliability: pd.DataFrame
    model_comparison: pd.DataFrame
    log_model: pd.DataFrame
    log_factorial: pd.DataFrame
    sensitivity: pd.DataFrame
    repetition: dict
    random_intercept: dict | None
    protocol: dict
    quality: dict
    validation: dict
    versions: dict
    fingerprint: dict
    generated_at: str


def _same_subject(header_value: str | None, subject: int) -> bool:
    if header_value is None or header_value == "":
        return False
    try:
        return int(float(header_value)) == int(subject)
    except ValueError:
        return False


def _far(header_value: float | None, recorded: float, tolerance: float) -> bool:
    if header_value is None or not np.isfinite(recorded):
        return False
    return abs(float(header_value) - float(recorded)) > tolerance


def _blank_metrics() -> dict[str, object]:
    return {
        "readable": False,
        "checksum_ok": False,
        "initial_ok": False,
        "n_samples": 0,
        "fs_hz": np.nan,
        "missing_channel": True,
        "subject_id_mismatch": True,
        "finite": False,
        "body_mass_ok": False,
        "fz_mean_n": np.nan,
        "fz_min_n": np.nan,
        "fz_ratio": np.nan,
        "cop_recon_cm": np.nan,
        "mv_cm_s": np.nan,
        "mv_ap_cm_s": np.nan,
        "mv_ml_cm_s": np.nan,
        "ellipse_cm2": np.nan,
        "max_step_cm": np.nan,
        "range_ap_cm": np.nan,
        "range_ml_cm": np.nan,
    }


def _evaluate_trial(raw_dir: Path, row) -> dict[str, object]:
    try:
        recording = read_recording(raw_dir / row.trial)
    except Exception:
        metrics = _blank_metrics()
        flags = quality_flags(metrics)
        return {
            "metrics": metrics,
            "flags": flags,
            "checksum_ok": False,
            "initial_ok": False,
            "header_age_mismatch": False,
            "header_height_mismatch": False,
            "header_weight_mismatch": False,
        }
    mismatch = not _same_subject(recording.header_subject, row.subject)
    metrics = metrics_from_physical(
        recording.physical,
        fs_hz=recording.fs_hz,
        n_samples=recording.n_samples,
        weight_kg=float(row.weight_kg),
        checksum_ok=recording.checksum_ok,
        initial_ok=recording.initial_ok,
        subject_id_mismatch=mismatch,
    )
    return {
        "metrics": metrics,
        "flags": quality_flags(metrics),
        "checksum_ok": recording.checksum_ok,
        "initial_ok": recording.initial_ok,
        "header_age_mismatch": _far(recording.header_age, row.age_years, 0.2),
        "header_height_mismatch": _far(recording.header_height, row.height_cm, 0.2),
        "header_weight_mismatch": _far(recording.header_weight, row.weight_kg, 0.2),
    }


def _read_trials(raw_dir: Path, metadata: pd.DataFrame) -> pd.DataFrame:
    missing = [
        trial
        for trial in metadata["trial"]
        if not (raw_dir / f"{trial}.dat").exists() or not (raw_dir / f"{trial}.hea").exists()
    ]
    if missing:
        raise FileNotFoundError(
            f"{len(missing)} recordings are missing from {raw_dir}. Download the database before analysis."
        )
    rows = []
    total = len(metadata)
    for index, row in enumerate(metadata.itertuples(index=False), start=1):
        evaluated = _evaluate_trial(raw_dir, row)
        if index % 250 == 0 or index == total:
            print(f"Read {index} of {total} trials", flush=True)
        metrics = evaluated["metrics"]
        flags = evaluated["flags"]
        rows.append(
            {
                "trial": row.trial,
                "subject": int(row.subject),
                "vision": row.vision,
                "surface": row.surface,
                "age_years": float(row.age_years),
                "age_group": row.age_group,
                "sex": row.sex,
                "height_cm": float(row.height_cm),
                "weight_kg": float(row.weight_kg),
                "bmi": float(row.bmi) if np.isfinite(row.bmi) else np.nan,
                "foot_len_cm": float(row.foot_len_cm) if np.isfinite(row.foot_len_cm) else np.nan,
                "self_reported_disability": bool(row.self_reported_disability),
                "n_samples": int(metrics["n_samples"]),
                "fs_hz": metrics["fs_hz"],
                "fz_mean_n": metrics["fz_mean_n"],
                "fz_min_n": metrics["fz_min_n"],
                "fz_ratio": metrics["fz_ratio"],
                "cop_recon_cm": metrics["cop_recon_cm"],
                "max_step_cm": metrics["max_step_cm"],
                "range_ap_cm": metrics["range_ap_cm"],
                "range_ml_cm": metrics["range_ml_cm"],
                "mv_cm_s": metrics["mv_cm_s"],
                "mv_ap_cm_s": metrics["mv_ap_cm_s"],
                "mv_ml_cm_s": metrics["mv_ml_cm_s"],
                "ellipse_cm2": metrics["ellipse_cm2"],
                "checksum_ok": bool(evaluated["checksum_ok"]),
                "initial_ok": bool(evaluated["initial_ok"]),
                "header_age_mismatch": bool(evaluated["header_age_mismatch"]),
                "header_height_mismatch": bool(evaluated["header_height_mismatch"]),
                "header_weight_mismatch": bool(evaluated["header_weight_mismatch"]),
                "exclude": bool(flags),
                "exclude_reasons": ";".join(flags),
            }
        )
    trials = pd.DataFrame(rows)
    valid = trials.loc[~trials["exclude"]].sort_values(["subject", "vision", "surface", "trial"]).copy()
    valid["rep_index"] = valid.groupby(["subject", "vision", "surface"], sort=False).cumcount()
    trials = trials.merge(valid[["trial", "rep_index"]], on="trial", how="left")
    trials["rep_index"] = trials["rep_index"].astype("Int64")
    assert_export_frame(trials)
    return trials[TRIAL_COLUMNS].copy()


def _reason_counts(trials: pd.DataFrame) -> dict[str, int]:
    counts: dict[str, int] = {}
    excluded = trials.loc[trials["exclude"], "exclude_reasons"]
    for text in excluded:
        for reason in str(text).split(";"):
            if reason:
                counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _package_versions() -> dict[str, str]:
    import matplotlib
    import scipy
    import statsmodels

    return {
        "python": sys.version.split()[0],
        "hbedb_sway": __version__,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pandas": pd.__version__,
        "statsmodels": statsmodels.__version__,
        "matplotlib": matplotlib.__version__,
    }


def _sensitivity_table(
    means: pd.DataFrame,
    n_boot: int,
    n_perm: int,
    seed: int,
) -> pd.DataFrame:
    pieces = []
    without_disability = means.loc[~means["self_reported_disability"]].copy()
    disability_frame = contrast_frame(without_disability, PRIMARY_OUTCOME)
    disability_summary = summarize_contrasts(
        disability_frame,
        PRIMARY_OUTCOME,
        n_boot,
        n_perm,
        seed + 17,
    )
    disability_summary.insert(0, "analysis", "Excluding self-reported disability")
    pieces.append(disability_summary)
    scaled = scale_by_foot_length(means)
    foot_frame = contrast_frame(scaled, PRIMARY_OUTCOME)
    foot_summary = summarize_contrasts(
        foot_frame,
        "mv_per_foot_length",
        n_boot,
        n_perm,
        seed + 29,
    )
    foot_summary.insert(0, "analysis", "Velocity divided by foot length")
    pieces.append(foot_summary)
    return pd.concat(pieces, ignore_index=True)


def _model_comparison(means: pd.DataFrame, trials: pd.DataFrame, bootstrap: pd.DataFrame) -> pd.DataFrame:
    subject_naive, subject_cluster, _subject_data = fit_factorial(means, PRIMARY_OUTCOME)
    trial_naive, trial_cluster, _trial_data = fit_factorial(trials, PRIMARY_OUTCOME)
    subject_table = factorial_contrast_table(subject_naive, subject_cluster).add_prefix("subject_")
    subject_table = subject_table.rename(
        columns={"subject_contrast": "contrast", "subject_contrast_label": "contrast_label"}
    )
    trial_table = factorial_contrast_table(trial_naive, trial_cluster).add_prefix("trial_")
    trial_table = trial_table.rename(columns={"trial_contrast": "contrast"})
    boot = bootstrap.loc[
        bootstrap["outcome"].eq(PRIMARY_OUTCOME),
        ["contrast", "contrast_label", "mean", "boot_se", "ci_low", "ci_high"],
    ]
    merged = boot.merge(subject_table, on=["contrast", "contrast_label"], how="left")
    merged = merged.merge(
        trial_table.drop(columns=["trial_contrast_label"]),
        on="contrast",
        how="left",
    )
    return merged


def _select_example_series(raw_dir: Path, means: pd.DataFrame, trials: pd.DataFrame) -> dict:
    firm_open = means[(means["vision"].eq("Open")) & (means["surface"].eq("Firm"))]
    median_speed = float(firm_open["mv_cm_s"].median())
    distances = (firm_open["mv_cm_s"] - median_speed).abs()
    subject = int(firm_open.iloc[int(distances.to_numpy().argmin())]["subject"])
    person = trials[(trials["subject"] == subject) & (~trials["exclude"])]
    series = {}
    for vision in ("Open", "Closed"):
        for surface in ("Firm", "Foam"):
            cell = person[(person["vision"].eq(vision)) & (person["surface"].eq(surface))].sort_values("rep_index")
            chosen = cell[cell["rep_index"] == 1]
            if chosen.empty:
                chosen = cell.iloc[[0]]
            recording = read_recording(raw_dir / str(chosen.iloc[0]["trial"]))
            series[(vision, surface)] = (
                recording.physical["COPx"],
                recording.physical["COPy"],
            )
    return series


def run_analysis(
    raw_dir: Path,
    output_dir: Path,
    results_path: Path | None = None,
    n_boot: int = BOOTSTRAP_REPLICATES,
    n_perm: int = PERMUTATION_REPLICATES,
    seed: int = RNG_SEED,
) -> AnalysisResult:
    raw_dir = Path(raw_dir)
    output_dir = Path(output_dir)
    table_dir = output_dir / "tables"
    figure_dir = output_dir / "figures"
    table_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)

    metadata = load_metadata(raw_dir / "BDSinfo.txt")
    protocol = protocol_gap_summary(metadata)
    trials = _read_trials(raw_dir, metadata)
    means = subject_condition_means(trials)
    analytic_ids = complete_subjects(means)
    means = means[means["subject"].isin(analytic_ids)].copy()
    analytic_trials = trials[trials["subject"].isin(analytic_ids) & (~trials["exclude"])].copy()

    contrast_parts = []
    age_parts = []
    descriptive_parts = []
    primary_frame = None
    for outcome in ALL_OUTCOMES:
        frame = contrast_frame(means, outcome)
        if outcome == PRIMARY_OUTCOME:
            primary_frame = frame
        contrast_parts.append(summarize_contrasts(frame, outcome, n_boot, n_perm, seed))
        age_parts.append(summarize_age_differences(frame, outcome, n_boot, n_perm, seed))
        descriptive_parts.append(condition_cell_means(means, outcome, n_boot, seed))
    if primary_frame is None:
        raise RuntimeError("Primary contrast frame was not created.")

    contrast_summary = pd.concat(contrast_parts, ignore_index=True)
    age_summary = pd.concat(age_parts, ignore_index=True)
    descriptive = pd.concat(descriptive_parts, ignore_index=True)
    slopes = age_slopes(primary_frame, PRIMARY_OUTCOME, n_boot, seed)
    sample = sample_description(primary_frame)
    sensitivity = _sensitivity_table(means, n_boot, n_perm, seed)
    foot_age = summarize_age_differences(
        contrast_frame(scale_by_foot_length(means), PRIMARY_OUTCOME),
        "mv_per_foot_length",
        n_boot,
        n_perm,
        seed + 29,
    )
    age_summary = pd.concat([age_summary, foot_age], ignore_index=True)
    reliability = repetition_reliability(analytic_trials, PRIMARY_OUTCOME)
    comparison = _model_comparison(means, analytic_trials, contrast_summary)
    log_model = fit_log_age_model(analytic_trials, PRIMARY_OUTCOME)
    log_input = analytic_trials.copy()
    log_input["log_mv"] = np.log(log_input[PRIMARY_OUTCOME].astype(float))
    log_naive, log_cluster, _log_data = fit_factorial(log_input, "log_mv")
    log_factorial = factorial_contrast_table(log_naive, log_cluster)
    log_factorial["ratio"] = np.exp(log_factorial["estimate"])
    log_factorial["ratio_ci_low"] = np.exp(log_factorial["ci_low"])
    log_factorial["ratio_ci_high"] = np.exp(log_factorial["ci_high"])
    repetition = repetition_coefficient(analytic_trials, PRIMARY_OUTCOME)
    random_intercept = random_intercept_icc(analytic_trials, PRIMARY_OUTCOME)

    included = trials.loc[~trials["exclude"]]
    rep_min = means.groupby("subject")["n_reps"].min()
    interaction_boot = contrast_summary[
        (contrast_summary["outcome"] == PRIMARY_OUTCOME) & (contrast_summary["contrast"] == PRIMARY_CONTRAST)
    ].iloc[0]
    interaction_model = comparison[comparison["contrast"] == PRIMARY_CONTRAST].iloc[0]
    interaction_values = primary_frame["interaction"].to_numpy(dtype=float)
    interaction_sd = float(interaction_values.std(ddof=1))
    quality = {
        "n_trials": int(len(trials)),
        "n_trials_excluded": int(trials["exclude"].sum()),
        "reason_counts": _reason_counts(trials),
        "n_subjects_metadata": int(metadata["subject"].nunique()),
        "n_subjects_analytic": int(primary_frame["subject"].nunique()),
        "n_analytic_trials": int(len(analytic_trials)),
        "n_subjects_with_fewer_than_3_reps": int((rep_min < 3).sum()),
        "fz_ratio_min": float(included["fz_ratio"].min()),
        "fz_ratio_max": float(included["fz_ratio"].max()),
        "cop_recon_max_cm": float(included["cop_recon_cm"].max()),
        "max_step_max_cm": float(included["max_step_cm"].max()),
        "speed_min_cm_s": float(included["mv_cm_s"].min()),
        "speed_max_cm_s": float(included["mv_cm_s"].max()),
        "n_checksum_fail": int((~trials["checksum_ok"]).sum()),
        "n_age_header_mismatch": int(trials["header_age_mismatch"].sum()),
        "n_height_header_mismatch": int(trials["header_height_mismatch"].sum()),
        "n_weight_header_mismatch": int(trials["header_weight_mismatch"].sum()),
        "n_subject_id_mismatch": int(trials["exclude_reasons"].str.contains("subject_id_mismatch").sum()),
    }
    validation = {
        "interaction_subject_mean": float(interaction_boot["mean"]),
        "interaction_subject_ols": float(interaction_model["subject_estimate"]),
        "interaction_trial_ols": float(interaction_model["trial_estimate"]),
        "se_trial_naive": float(interaction_model["trial_se_naive"]),
        "se_trial_cluster": float(interaction_model["trial_se_cluster"]),
        "se_subject_naive": float(interaction_model["subject_se_naive"]),
        "se_subject_cluster": float(interaction_model["subject_se_cluster"]),
        "se_bootstrap": float(interaction_boot["boot_se"]),
        "contrast_sd": interaction_sd,
        "se_participants": interaction_sd / np.sqrt(interaction_values.size),
        "se_if_trials_counted_as_people": interaction_sd / np.sqrt(len(analytic_trials)),
        "t_ci_low": float(interaction_boot["t_ci_low"]),
        "t_ci_high": float(interaction_boot["t_ci_high"]),
        "boot_ci_low": float(interaction_boot["ci_low"]),
        "boot_ci_high": float(interaction_boot["ci_high"]),
    }

    people = primary_frame.drop_duplicates("subject")
    plot_age_distribution(people, figure_dir / "age_distribution.png")
    plot_quality(trials, figure_dir / "quality_checks.png")
    plot_condition_means(descriptive, figure_dir / "condition_means.png", PRIMARY_OUTCOME)
    plot_condition_means_by_age(descriptive, figure_dir / "condition_means_by_age.png", PRIMARY_OUTCOME)
    plot_forest(
        contrast_summary,
        figure_dir / "forest_mean_velocity.png",
        PRIMARY_OUTCOME,
        "Change in resultant mean velocity (cm/s), 95% bootstrap CI",
        "Within-subject contrasts, one participant one vote",
    )
    plot_age_forest(age_summary, figure_dir / "forest_age_differences.png", PRIMARY_OUTCOME)
    plot_axis_forest(contrast_summary, figure_dir / "forest_axes.png")
    plot_forest(
        contrast_summary,
        figure_dir / "forest_ellipse.png",
        "ellipse_cm2",
        "Change in 95% prediction ellipse area (cm^2), 95% bootstrap CI",
        "Within-subject contrasts for sway area",
    )
    slope_row = slopes[slopes["contrast"] == PRIMARY_CONTRAST].iloc[0]
    plot_interaction_against_age(
        primary_frame,
        float(slope_row["slope_per_year"]),
        figure_dir / "interaction_vs_age.png",
    )
    plot_contrast_distribution(primary_frame, figure_dir / "interaction_distribution.png")
    plot_stabilograms(_select_example_series(raw_dir, means, analytic_trials), figure_dir / "example_stabilogram.png")

    trials.to_csv(table_dir / "trial_metrics.csv", index=False)
    means.to_csv(table_dir / "subject_condition_means.csv", index=False)
    primary_frame.to_csv(table_dir / "subject_contrasts_mean_velocity.csv", index=False)
    contrast_summary.to_csv(table_dir / "contrasts.csv", index=False)
    age_summary.to_csv(table_dir / "age_differences.csv", index=False)
    slopes.to_csv(table_dir / "age_slopes.csv", index=False)
    descriptive.to_csv(table_dir / "condition_descriptives.csv", index=False)
    sample.to_csv(table_dir / "sample.csv", index=False)
    reliability.to_csv(table_dir / "reliability.csv", index=False)
    comparison.to_csv(table_dir / "model_comparison.csv", index=False)
    log_model.to_csv(table_dir / "log_cluster_model.csv", index=False)
    log_factorial.to_csv(table_dir / "log_factorial.csv", index=False)
    sensitivity.to_csv(table_dir / "sensitivity.csv", index=False)

    versions = _package_versions()
    fingerprint = {
        "bdsinfo_sha256": _sha256(raw_dir / "BDSinfo.txt"),
        "records_sha256": _sha256(raw_dir / "RECORDS"),
        "dataset_version": DATASET_VERSION,
        "dataset_doi": DATASET_DOI,
        "license_followed": LICENSE_SHORT,
        "seed": seed,
        "n_bootstrap": n_boot,
        "n_permutation": n_perm,
    }
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    result = AnalysisResult(
        trials=trials,
        means=means,
        contrasts=primary_frame,
        contrast_summary=contrast_summary,
        age_summary=age_summary,
        age_slopes=slopes,
        descriptive=descriptive,
        sample=sample,
        reliability=reliability,
        model_comparison=comparison,
        log_model=log_model,
        log_factorial=log_factorial,
        sensitivity=sensitivity,
        repetition=repetition,
        random_intercept=random_intercept,
        protocol=protocol,
        quality=quality,
        validation=validation,
        versions=versions,
        fingerprint=fingerprint,
        generated_at=generated_at,
    )
    metadata_path = output_dir / "run_metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "generated_at": generated_at,
                "versions": versions,
                "fingerprint": fingerprint,
                "quality": quality,
                "validation": validation,
                "protocol": protocol,
                "repetition": repetition,
                "random_intercept": random_intercept,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    if results_path is not None:
        write_results(result, Path(results_path))
    return result
