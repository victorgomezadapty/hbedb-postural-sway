"""Figures for the subject-level sway analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

FIRM = "#0072B2"
FOAM = "#D55E00"
YOUNG = "#009E73"
OLDER = "#CC79A7"
INK = "#1f1f1f"
MUTED = "#5c5c5c"
ZERO = "#888888"

_STYLE = {
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "text.color": INK,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "axes.titlesize": 12,
    "axes.labelsize": 11,
}


def _save(fig: plt.Figure, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


def plot_age_distribution(subjects: pd.DataFrame, path: Path) -> None:
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        ages = subjects["age_years"].to_numpy(dtype=float)
        bins = np.arange(15, 95, 5)
        ax.hist(ages, bins=bins, color="#4C78A8", edgecolor="white")
        ax.axvline(60, color=INK, linestyle="--", linewidth=1)
        ax.set_xlabel("Age (years)")
        ax.set_ylabel("Participants")
        ax.set_title("Age in the analytic sample")
        ax.text(61, ax.get_ylim()[1] * 0.92, "Source cutoff, 60 years", color=MUTED, fontsize=9)
        _save(fig, path)


def plot_quality(trials: pd.DataFrame, path: Path) -> None:
    with plt.rc_context(_STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(8.6, 4.0))
        ratio = trials["fz_ratio"].to_numpy(dtype=float)
        ratio = ratio[np.isfinite(ratio)]
        axes[0].hist(ratio, bins=30, color="#4C78A8", edgecolor="white")
        axes[0].axvline(0.75, color=FOAM, linestyle="--", linewidth=1)
        axes[0].axvline(1.25, color=FOAM, linestyle="--", linewidth=1)
        axes[0].set_xlabel("Mean vertical force / body weight")
        axes[0].set_ylabel("Trials")
        axes[0].set_title("Vertical force check")
        step = trials["max_step_cm"].to_numpy(dtype=float)
        step = step[np.isfinite(step)]
        axes[1].hist(step, bins=30, color="#4C78A8", edgecolor="white")
        axes[1].set_xlabel("Largest sample-to-sample COP step (cm)")
        axes[1].set_ylabel("Trials")
        largest = float(np.max(step)) if step.size else float("nan")
        axes[1].set_title(f"Largest observed step {largest:.2f} cm; threshold 2 cm")
        _save(fig, path)


def plot_condition_means(descriptive: pd.DataFrame, path: Path, outcome: str = "mv_cm_s") -> None:
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(6.4, 4.4))
        _draw_condition_lines(ax, descriptive, "All", outcome)
        ax.set_ylabel("Resultant mean velocity (cm/s)")
        ax.set_title("Participant means by vision and surface")
        ax.set_xlabel("Error bars: 95% bootstrap CI across participants")
        ax.legend(frameon=False)
        _save(fig, path)


def plot_condition_means_by_age(descriptive: pd.DataFrame, path: Path, outcome: str = "mv_cm_s") -> None:
    with plt.rc_context(_STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(8.8, 4.3), sharey=True)
        for ax, group, title in (
            (axes[0], "Young", "Younger than 60 years"),
            (axes[1], "Old", "60 years or older"),
        ):
            _draw_condition_lines(ax, descriptive, group, outcome)
            ax.set_title(title)
            ax.set_ylabel("Resultant mean velocity (cm/s)" if ax is axes[0] else "")
        axes[1].legend(frameon=False, loc="upper left")
        fig.suptitle("Error bars: 95% bootstrap CI across participants", fontsize=11)
        _save(fig, path)


def _draw_condition_lines(ax, descriptive: pd.DataFrame, group: str, outcome: str) -> None:
    subset = descriptive[(descriptive["outcome"] == outcome) & (descriptive["age_group"] == group)]
    x = np.array([0.0, 1.0])
    for surface, color, shift, marker in (
        ("Firm", FIRM, -0.03, "o"),
        ("Foam", FOAM, 0.03, "s"),
    ):
        rows = []
        for vision in ("Open", "Closed"):
            row = subset[(subset["vision"] == vision) & (subset["surface"] == surface)].iloc[0]
            rows.append(row)
        means = np.array([row["mean"] for row in rows])
        low = np.array([row["ci_low"] for row in rows])
        high = np.array([row["ci_high"] for row in rows])
        ax.errorbar(
            x + shift,
            means,
            yerr=np.vstack([means - low, high - means]),
            color=color,
            marker=marker,
            linewidth=1.6,
            capsize=3,
            label="Firm" if surface == "Firm" else "Foam",
        )
    ax.set_xticks([0, 1], ["Eyes open", "Eyes closed"])
    ax.set_xlim(-0.25, 1.25)


def plot_forest(summary: pd.DataFrame, path: Path, outcome: str, xlabel: str, title: str) -> None:
    with plt.rc_context(_STYLE):
        subset = summary[summary["outcome"] == outcome].copy()
        order = [key for key, _label in (
            ("vision_on_firm", ""),
            ("vision_on_foam", ""),
            ("surface_eyes_open", ""),
            ("surface_eyes_closed", ""),
            ("interaction", ""),
        )]
        subset["order"] = subset["contrast"].map({key: index for index, key in enumerate(order)})
        subset = subset.sort_values("order", ascending=True)
        fig, ax = plt.subplots(figsize=(8.2, 4.6))
        y = np.arange(len(subset))
        for position, (_, row) in enumerate(subset.iterrows()):
            color = FOAM if row["contrast"] == "interaction" else FIRM
            marker = "D" if row["contrast"] == "interaction" else "o"
            ax.plot([row["ci_low"], row["ci_high"]], [position, position], color=color, linewidth=1.8)
            ax.plot(row["mean"], position, marker=marker, color=color, markersize=7)
        ax.axvline(0, color=ZERO, linewidth=1)
        ax.set_yticks(y, subset["contrast_label"])
        ax.set_xlabel(xlabel)
        ax.set_title(title)
        _save(fig, path)


def plot_age_forest(age_summary: pd.DataFrame, path: Path, outcome: str) -> None:
    plot_forest(
        age_summary.rename(columns={"diff_old_minus_young": "mean"}),
        path,
        outcome,
        "Older minus younger (cm/s), 95% bootstrap CI",
        "Age difference in the within-subject contrasts",
    )


def plot_axis_forest(summary: pd.DataFrame, path: Path) -> None:
    with plt.rc_context(_STYLE):
        fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.6), sharey=True)
        for ax, outcome, title in (
            (axes[0], "mv_ap_cm_s", "Anteroposterior"),
            (axes[1], "mv_ml_cm_s", "Mediolateral"),
        ):
            subset = summary[summary["outcome"] == outcome].copy()
            order = ["vision_on_firm", "vision_on_foam", "surface_eyes_open", "surface_eyes_closed", "interaction"]
            subset["order"] = subset["contrast"].map({key: index for index, key in enumerate(order)})
            subset = subset.sort_values("order", ascending=True)
            for position, (_, row) in enumerate(subset.iterrows()):
                color = FOAM if row["contrast"] == "interaction" else FIRM
                ax.plot([row["ci_low"], row["ci_high"]], [position, position], color=color, linewidth=1.6)
                ax.plot(row["mean"], position, "o", color=color, markersize=6)
            ax.axvline(0, color=ZERO, linewidth=1)
            ax.set_title(title)
            ax.set_xlabel("Change (cm/s), 95% bootstrap CI")
            if ax is axes[0]:
                ax.set_yticks(np.arange(len(subset)), subset["contrast_label"])
        _save(fig, path)


def plot_interaction_against_age(frame: pd.DataFrame, slope: float, path: Path) -> None:
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(7.2, 4.6))
        for group, color, label in (
            ("Young", YOUNG, "Younger than 60"),
            ("Old", OLDER, "60 or older"),
        ):
            subset = frame[frame["age_group"].eq(group)]
            ax.scatter(
                subset["age_years"],
                subset["interaction"],
                s=28,
                color=color,
                alpha=0.8,
                label=label,
                linewidths=0,
            )
        ages = frame["age_years"].to_numpy(dtype=float)
        x_line = np.linspace(float(ages.min()), float(ages.max()), 50)
        intercept = float(frame["interaction"].mean() - slope * ages.mean())
        ax.plot(x_line, intercept + slope * x_line, color=INK, linewidth=1.4)
        ax.axhline(0, color=ZERO, linewidth=1)
        ax.set_xlabel("Age (years)")
        ax.set_ylabel("Interaction (cm/s)")
        ax.set_title("Within-subject interaction against age\nLine: least-squares fit. Each point is one participant.")
        ax.legend(frameon=False)
        _save(fig, path)


def plot_contrast_distribution(frame: pd.DataFrame, path: Path) -> None:
    with plt.rc_context(_STYLE):
        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        values = frame["interaction"].to_numpy(dtype=float)
        ax.hist(values, bins=20, color="#4C78A8", edgecolor="white")
        ax.axvline(0, color=ZERO, linewidth=1)
        ax.axvline(float(values.mean()), color=FOAM, linewidth=1.6, label="Mean")
        ax.set_xlabel("Interaction (cm/s)")
        ax.set_ylabel("Participants")
        ax.set_title("Distribution of the within-subject interaction")
        ax.legend(frameon=False)
        _save(fig, path)


def plot_stabilograms(series: dict[tuple[str, str], tuple[np.ndarray, np.ndarray]], path: Path) -> None:
    with plt.rc_context(_STYLE):
        fig, axes = plt.subplots(2, 2, figsize=(7.4, 7.2), sharex=True, sharey=True)
        layout = (
            ((0, 0), "Open", "Firm", "Firm, eyes open"),
            ((0, 1), "Closed", "Firm", "Firm, eyes closed"),
            ((1, 0), "Open", "Foam", "Foam, eyes open"),
            ((1, 1), "Closed", "Foam", "Foam, eyes closed"),
        )
        centered = {}
        limit = 0.1
        for _position, vision, surface, _title in layout:
            x, y = series[(vision, surface)]
            x = np.asarray(x, dtype=float) - float(np.mean(x))
            y = np.asarray(y, dtype=float) - float(np.mean(y))
            centered[(vision, surface)] = (x, y)
            limit = max(limit, float(np.max(np.abs(x))), float(np.max(np.abs(y))))
        limit *= 1.08
        for position, vision, surface, title in layout:
            ax = axes[position]
            x, y = centered[(vision, surface)]
            ax.plot(y, x, color=FIRM if surface == "Firm" else FOAM, linewidth=0.7)
            ax.axhline(0, color="#dddddd", linewidth=0.6)
            ax.axvline(0, color="#dddddd", linewidth=0.6)
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlim(-limit, limit)
            ax.set_ylim(-limit, limit)
            ax.set_title(title)
            if position[0] == 1:
                ax.set_xlabel("Mediolateral (cm)")
            if position[1] == 0:
                ax.set_ylabel("Anteroposterior (cm)")
        fig.suptitle(
            "Demeaned COP from one participant near the median\nShared scale. Illustration only, not a sample summary.",
            fontsize=12,
        )
        _save(fig, path)
