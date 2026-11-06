"""Metadata, subject-level means, and within-subject contrasts.

Trials are nested in participants. Every inferential table produced here has
one row per participant, or one row per participant and condition.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from hbedb_sway.constants import ALL_OUTCOMES, BANNED_EXPORT_COLUMNS, CONTRASTS, KEPT_METADATA

_RENAME = {
    "Trial": "trial",
    "Subject": "subject",
    "Vision": "vision",
    "Surface": "surface",
    "Age": "age_years",
    "AgeGroup": "age_group",
    "Gender": "sex",
    "Height": "height_cm",
    "Weight": "weight_kg",
    "BMI": "bmi",
    "FootLen": "foot_len_cm",
    "Disability": "self_reported_disability",
}


def assert_export_frame(frame: pd.DataFrame) -> None:
    banned_hits = sorted(set(frame.columns.str.lower()) & BANNED_EXPORT_COLUMNS)
    if banned_hits:
        raise RuntimeError(f"Export frame contains sensitive columns: {banned_hits}")
    for column in frame.columns:
        lowered = column.lower()
        if lowered.startswith(("fes_", "ipaq_", "tmt_", "best_", "illness", "medic")):
            raise RuntimeError(f"Export frame contains a sensitive column: {column}")


def load_metadata(path: Path) -> pd.DataFrame:
    """Read the analysis columns from BDSinfo and drop everything else."""
    frame = pd.read_csv(
        path,
        sep="\t",
        usecols=list(KEPT_METADATA),
        dtype=str,
        encoding="utf-8",
    )
    frame = frame.rename(columns=_RENAME)
    frame["subject"] = frame["subject"].astype(int)
    for column in ("age_years", "height_cm", "weight_kg", "bmi", "foot_len_cm"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["vision"] = frame["vision"].str.strip()
    frame["surface"] = frame["surface"].str.strip()
    frame["age_group"] = frame["age_group"].str.strip()
    frame["sex"] = frame["sex"].str.strip()
    frame["trial"] = frame["trial"].str.strip()
    frame["self_reported_disability"] = frame["self_reported_disability"].str.strip().eq("Yes")
    unexpected_vision = sorted(set(frame["vision"]) - {"Open", "Closed"})
    unexpected_surface = sorted(set(frame["surface"]) - {"Firm", "Foam"})
    unexpected_age = sorted(set(frame["age_group"]) - {"Young", "Old"})
    if unexpected_vision or unexpected_surface or unexpected_age:
        raise ValueError(
            "Unexpected design labels: "
            f"vision {unexpected_vision}, surface {unexpected_surface}, age {unexpected_age}."
        )
    if not (frame.loc[frame["age_group"].eq("Young"), "age_years"] < 60).all():
        raise ValueError("A Young label has age of 60 years or more.")
    if not (frame.loc[frame["age_group"].eq("Old"), "age_years"] >= 60).all():
        raise ValueError("An Old label has age below 60 years.")
    assert_export_frame(frame)
    return frame


def subject_condition_means(trials: pd.DataFrame) -> pd.DataFrame:
    """Average valid repetitions. One row per participant and condition."""
    kept = trials.loc[~trials["exclude"]].copy()
    if kept.empty:
        raise ValueError("No valid trials remain after quality control.")
    group_cols = ["subject", "vision", "surface"]
    means = kept.groupby(group_cols, as_index=False)[list(ALL_OUTCOMES)].mean()
    reps = kept.groupby(group_cols, as_index=False).size().rename(columns={"size": "n_reps"})
    demo_cols = [
        "age_years",
        "age_group",
        "sex",
        "height_cm",
        "weight_kg",
        "bmi",
        "foot_len_cm",
        "self_reported_disability",
    ]
    demo = kept.groupby("subject", as_index=False)[demo_cols].first()
    out = means.merge(reps, on=group_cols).merge(demo, on="subject")
    assert_export_frame(out)
    return out


def complete_subjects(means: pd.DataFrame) -> pd.Index:
    cells = means["vision"].astype(str) + "|" + means["surface"].astype(str)
    counts = cells.groupby(means["subject"]).nunique()
    return counts[counts == 4].index


def contrast_frame(means: pd.DataFrame, outcome: str) -> pd.DataFrame:
    """Within-subject contrasts for participants who have all four conditions."""
    eligible = means[means["subject"].isin(complete_subjects(means))].copy()
    wide = eligible.pivot(index="subject", columns=["vision", "surface"], values=outcome)
    for key in (("Open", "Firm"), ("Closed", "Firm"), ("Open", "Foam"), ("Closed", "Foam")):
        if key not in wide.columns:
            raise ValueError(f"Condition {key} is missing from the subject means.")
    firm_open = wide[("Open", "Firm")]
    firm_closed = wide[("Closed", "Firm")]
    foam_open = wide[("Open", "Foam")]
    foam_closed = wide[("Closed", "Foam")]
    frame = pd.DataFrame(
        {
            "subject": wide.index.astype(int),
            "vision_on_firm": firm_closed - firm_open,
            "vision_on_foam": foam_closed - foam_open,
            "surface_eyes_open": foam_open - firm_open,
            "surface_eyes_closed": foam_closed - firm_closed,
        }
    )
    frame["interaction"] = frame["vision_on_foam"] - frame["vision_on_firm"]
    # The two algebraic forms of the interaction must agree.
    alternate = frame["surface_eyes_closed"] - frame["surface_eyes_open"]
    if not np.allclose(frame["interaction"].to_numpy(), alternate.to_numpy()):
        raise RuntimeError("Interaction algebra is inconsistent.")
    demo = eligible.drop_duplicates("subject").set_index("subject")
    for column in (
        "age_group",
        "age_years",
        "sex",
        "height_cm",
        "weight_kg",
        "foot_len_cm",
        "self_reported_disability",
    ):
        frame[column] = frame["subject"].map(demo[column])
    frame["outcome"] = outcome
    return frame.reset_index(drop=True)


def scale_by_foot_length(means: pd.DataFrame) -> pd.DataFrame:
    scaled = means.dropna(subset=["foot_len_cm"]).copy()
    if (scaled["foot_len_cm"] <= 0).any():
        raise ValueError("Foot length must be positive.")
    for outcome in ALL_OUTCOMES:
        scaled[outcome] = scaled[outcome] / scaled["foot_len_cm"]
    return scaled


def sample_description(subjects: pd.DataFrame) -> pd.DataFrame:
    rows = []
    groups = [
        ("All", "All analytic participants", subjects),
        ("Young", "Younger than 60 years", subjects[subjects["age_group"].eq("Young")]),
        ("Old", "60 years or older", subjects[subjects["age_group"].eq("Old")]),
    ]
    for code, label, group in groups:
        rows.append(
            {
                "group": code,
                "group_label": label,
                "n": int(len(group)),
                "n_female": int(group["sex"].eq("F").sum()),
                "n_male": int(group["sex"].eq("M").sum()),
                "age_min": float(group["age_years"].min()),
                "age_median": float(group["age_years"].median()),
                "age_max": float(group["age_years"].max()),
                "height_cm_mean": float(group["height_cm"].mean()),
                "weight_kg_mean": float(group["weight_kg"].mean()),
                "foot_len_cm_mean": float(group["foot_len_cm"].mean()),
                "n_disability": int(group["self_reported_disability"].sum()),
                "n_missing_foot": int(group["foot_len_cm"].isna().sum()),
            }
        )
    return pd.DataFrame(rows)


def protocol_gap_summary(metadata: pd.DataFrame) -> dict[str, object]:
    cells = metadata["vision"].astype(str) + "|" + metadata["surface"].astype(str)
    counts = cells.groupby(metadata["subject"]).nunique()
    incomplete_ids = counts[counts < 4].index
    people = metadata.drop_duplicates("subject")
    incomplete = people[people["subject"].isin(incomplete_ids)]
    by_age = incomplete.groupby("age_group").size().to_dict()
    required = {"Open|Firm", "Closed|Firm", "Open|Foam", "Closed|Foam"}
    missing: dict[str, int] = {key: 0 for key in sorted(required)}
    for _, group in cells.groupby(metadata["subject"]):
        absent = required - set(group)
        for key in absent:
            missing[key] += 1
    return {
        "n_incomplete_subjects": int(len(incomplete_ids)),
        "incomplete_by_age": {str(key): int(value) for key, value in by_age.items()},
        "missing_cells": missing,
        "n_subjects": int(people["subject"].nunique()),
        "n_trials": int(len(metadata)),
    }


def contrast_labels() -> dict[str, str]:
    return dict(CONTRASTS)
