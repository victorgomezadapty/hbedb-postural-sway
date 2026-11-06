"""Write the results summary from an AnalysisResult.

Numbers are taken from the fitted objects. The prose is checked for em dashes,
en dashes, and double hyphens before it is written.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from hbedb_sway.constants import OUTCOME_LABELS, OUTCOME_UNITS
from hbedb_sway.punctuation import assert_plain_prose
from hbedb_sway.qc import REASON_LABELS


def _num(value: float, digits: int = 2) -> str:
    return f"{float(value):.{digits}f}"


def _p(value: float) -> str:
    if value < 0.001:
        return "p < 0.001"
    if value < 0.010:
        return f"p = {value:.4f}"
    return f"p = {value:.3f}"


def _ci(row, estimate_key: str = "mean", digits: int = 2, unit: str = "") -> str:
    unit_text = f" {unit}" if unit else ""
    return (
        f"{_num(row[estimate_key], digits)}{unit_text} "
        f"(95% CI {_num(row['ci_low'], digits)} to {_num(row['ci_high'], digits)})"
    )


def _pick(frame: pd.DataFrame, outcome: str, contrast: str) -> pd.Series:
    match = frame[(frame["outcome"] == outcome) & (frame["contrast"] == contrast)]
    if match.empty:
        raise KeyError(f"Missing result row {outcome} / {contrast}")
    return match.iloc[0]


def _cell(descriptive: pd.DataFrame, outcome: str, group: str, vision: str, surface: str) -> pd.Series:
    match = descriptive[
        (descriptive["outcome"] == outcome)
        & (descriptive["age_group"] == group)
        & (descriptive["vision"] == vision)
        & (descriptive["surface"] == surface)
    ]
    return match.iloc[0]


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _sample_table(sample: pd.DataFrame) -> str:
    rows = []
    for _, row in sample.iterrows():
        rows.append(
            [
                str(row["group_label"]),
                str(int(row["n"])),
                str(int(row["n_female"])),
                str(int(row["n_male"])),
                f"{_num(row['age_min'], 1)} to {_num(row['age_max'], 1)}",
                _num(row["age_median"], 1),
                _num(row["height_cm_mean"], 1),
                _num(row["weight_kg_mean"], 1),
                str(int(row["n_disability"])),
            ]
        )
    return _markdown_table(
        ["Group", "n", "Female", "Male", "Age range (years)", "Median age", "Mean height (cm)", "Mean mass (kg)", "Disability flag"],
        rows,
    )


def _contrast_table(summary: pd.DataFrame, outcome: str, unit: str) -> str:
    subset = summary[summary["outcome"] == outcome]
    rows = []
    for _, row in subset.iterrows():
        rows.append(
            [
                str(row["contrast_label"]),
                _num(row["mean"]),
                f"{_num(row['ci_low'])} to {_num(row['ci_high'])}",
                _num(row["median"]),
                f"{int(row['n_positive'])} of {int(row['n_subjects'])}",
                _p(row["perm_p"]),
            ]
        )
    return _markdown_table(
        ["Contrast", f"Mean ({unit})", "95% CI", "Median", "Positive contrasts", "Sign-flip p"],
        rows,
    )


def _age_table(summary: pd.DataFrame, outcome: str, unit: str) -> str:
    subset = summary[summary["outcome"] == outcome]
    rows = []
    for _, row in subset.iterrows():
        rows.append(
            [
                str(row["contrast_label"]),
                _num(row["diff_old_minus_young"]),
                f"{_num(row['ci_low'])} to {_num(row['ci_high'])}",
                _p(row["perm_p"]),
            ]
        )
    return _markdown_table(
        ["Contrast", f"Older minus younger ({unit})", "95% CI", "Permutation p"],
        rows,
    )


def _condition_table(descriptive: pd.DataFrame, outcome: str, group: str) -> str:
    rows = []
    for surface in ("Firm", "Foam"):
        for vision, vision_label in (("Open", "Eyes open"), ("Closed", "Eyes closed")):
            row = _cell(descriptive, outcome, group, vision, surface)
            rows.append(
                [
                    surface,
                    vision_label,
                    str(int(row["n"])),
                    _num(row["mean"]),
                    f"{_num(row['ci_low'])} to {_num(row['ci_high'])}",
                    _num(row["median"]),
                    f"{_num(row['q25'])} to {_num(row['q75'])}",
                ]
            )
    return _markdown_table(
        ["Surface", "Vision", "n", "Mean (cm/s)", "95% CI", "Median", "IQR"],
        rows,
    )


def _missing_cell_sentence(protocol: dict) -> str:
    labels = {
        "Open|Firm": "firm surface with eyes open",
        "Closed|Firm": "firm surface with eyes closed",
        "Open|Foam": "foam with eyes open",
        "Closed|Foam": "foam with eyes closed",
    }
    parts = []
    for key, count in protocol["missing_cells"].items():
        if int(count) > 0:
            parts.append(f"{labels.get(key, key)} ({int(count)})")
    if not parts:
        return "No recorded condition cell was absent."
    return "Absent condition cells, counting participants, were " + ", ".join(parts) + "."


def render_results(result) -> str:
    quality = result.quality
    validation = result.validation
    protocol = result.protocol
    n_people = int(quality["n_subjects_analytic"])
    n_recruited = int(quality["n_subjects_metadata"])
    n_trials = int(quality["n_trials"])
    primary = _pick(result.contrast_summary, "mv_cm_s", "interaction")
    firm_open = _cell(result.descriptive, "mv_cm_s", "All", "Open", "Firm")
    foam_closed = _cell(result.descriptive, "mv_cm_s", "All", "Closed", "Foam")
    sample_all = result.sample[result.sample["group"] == "All"].iloc[0]
    sample_young = result.sample[result.sample["group"] == "Young"].iloc[0]
    sample_old = result.sample[result.sample["group"] == "Old"].iloc[0]
    log_interaction = result.log_factorial[result.log_factorial["contrast"] == "interaction"].iloc[0]
    log_age = result.log_model[result.log_model["term"] == "interaction_old_minus_young"].iloc[0]
    slope = result.age_slopes[result.age_slopes["contrast"] == "interaction"].iloc[0]
    disability = result.sensitivity[
        (result.sensitivity["analysis"] == "Excluding self-reported disability")
        & (result.sensitivity["contrast"] == "interaction")
    ].iloc[0]
    foot = result.sensitivity[
        (result.sensitivity["analysis"] == "Velocity divided by foot length")
        & (result.sensitivity["contrast"] == "interaction")
    ].iloc[0]
    icc_min = float(result.reliability["icc"].min()) if len(result.reliability) else float("nan")
    icc_max = float(result.reliability["icc"].max()) if len(result.reliability) else float("nan")
    sem_min = float(result.reliability["sem_cm_s"].min()) if len(result.reliability) else float("nan")
    sem_max = float(result.reliability["sem_cm_s"].max()) if len(result.reliability) else float("nan")
    young_incomplete = int(protocol["incomplete_by_age"].get("Young", 0))
    old_incomplete = int(protocol["incomplete_by_age"].get("Old", 0))
    reason_text = "none"
    if quality["reason_counts"]:
        reason_text = "; ".join(
            f"{REASON_LABELS.get(key, key)} ({value})"
            for key, value in quality["reason_counts"].items()
        )
    if quality["n_trials_excluded"] == 0:
        qc_sentence = "Quality control excluded no trials."
    else:
        qc_sentence = f"Quality control excluded {quality['n_trials_excluded']} trials ({reason_text})."
    if quality["n_subjects_with_fewer_than_3_reps"] == 0:
        repetition_coverage = "Every analytic participant had three valid repetitions in every condition."
    else:
        repetition_coverage = (
            f"{quality['n_subjects_with_fewer_than_3_reps']} analytic participants had fewer than "
            "three valid repetitions in a condition."
        )
    recon = float(quality["cop_recon_max_cm"])
    recon_text = f"{recon:.2e} cm" if recon < 1e-4 else f"{recon:.4f} cm"
    estimate_gap = abs(validation["interaction_subject_mean"] - validation["interaction_subject_ols"])
    trial_gap = abs(validation["interaction_subject_mean"] - validation["interaction_trial_ols"])
    t_gap = max(
        abs(validation["t_ci_low"] - validation["boot_ci_low"]),
        abs(validation["t_ci_high"] - validation["boot_ci_high"]),
    )
    if result.random_intercept is None:
        icc_sentence = "A random-intercept model did not return a usable variance estimate."
    else:
        icc_sentence = (
            "After the four condition means were included, a random-intercept model "
            f"attributed {_num(100 * result.random_intercept['icc'], 1)}% of the remaining variance "
            "to stable differences between participants. "
            + (
                "The fit converged."
                if result.random_intercept.get("converged")
                else "The optimizer did not report convergence."
            )
        )
    secondary_lines = []
    for outcome in ("mv_ap_cm_s", "mv_ml_cm_s", "ellipse_cm2"):
        row = _pick(result.contrast_summary, outcome, "interaction")
        secondary_lines.append(
            f"{OUTCOME_LABELS[outcome]} interaction: {_ci(row, unit=OUTCOME_UNITS[outcome])}, {_p(row['perm_p'])}."
        )
    lines = [
        "# Vision, support surface, and age in quiet-stance postural sway",
        "",
        "Analysis by Víctor Andrés Gómez López.",
        "",
        "This is an independent analysis of the Human Balance Evaluation Database, version 1.0.0. "
        "It estimates how vision and the support surface change quiet-stance center-of-pressure sway, "
        "and whether those within-person changes differ between the age groups defined by the source study. "
        "It does not estimate a treatment effect, a diagnostic cutoff, or a training recommendation.",
        "",
        "## Question",
        "",
        "In adults who completed the four quiet-stance conditions, how much does resultant "
        "center-of-pressure mean velocity change when the eyes are closed and when a firm surface "
        "is replaced by foam, and is the effect of closing the eyes larger on foam than on the firm surface? "
        "The secondary question is whether those within-person changes differ between adults younger than 60 years "
        "and adults aged 60 years or older, which is the age grouping supplied with the database.",
        "",
        "The primary estimand is the interaction for resultant mean velocity, in cm/s. "
        "It equals the eyes-closed minus eyes-open difference on foam, minus the same difference on the firm surface. "
        "A positive value means that closing the eyes adds more velocity on foam than on the firm surface. "
        "The four simple effects are the planned decomposition of that interaction, not a separate family of primary tests. "
        "Anteroposterior velocity, mediolateral velocity, and the 95% prediction ellipse area are secondary outcomes. "
        "Age comparisons are secondary.",
        "",
        "## Sample and unit of analysis",
        "",
        f"The database contains {n_trials:,} stored trials from {n_recruited} participants. "
        f"A complete protocol is 12 trials: three repetitions of each of four conditions. "
        f"There were {protocol['n_incomplete_subjects']} participants without all four conditions "
        f"({young_incomplete} in the younger group and {old_incomplete} in the older group). "
        f"{_missing_cell_sentence(protocol)} "
        "Santos and Duarte (2016) state that these trials are missing because the participant could not complete 60 s. "
        "The primary contrasts use only participants with at least one valid trial in every condition, "
        f"which is {n_people} people and {quality['n_analytic_trials']:,} trials. "
        f"{qc_sentence} {repetition_coverage} "
        "Each participant then contributes the mean of the available repetitions in that condition. "
        "Every interval below resamples or clusters those participants. "
        f"The {n_trials:,} trials are not treated as {n_trials:,} independent people.",
        "",
        _sample_table(result.sample),
        "",
        f"The analytic sample has {int(sample_all['n_female'])} women and {int(sample_all['n_male'])} men. "
        f"The older group has {int(sample_old['n_female'])} women and {int(sample_old['n_male'])} men, "
        f"so the age comparison is not balanced by sex. "
        f"{int(sample_all['n_disability'])} analytic participants have the source disability flag "
        "(Disability = Yes in BDSinfo; the free-text description is not used or shown). "
        "Ages run from "
        f"{_num(sample_young['age_min'], 1)} to {_num(sample_young['age_max'], 1)} years in the younger group "
        f"and from {_num(sample_old['age_min'], 1)} to {_num(sample_old['age_max'], 1)} years in the older group. "
        "The source paper notes that the ages fall mainly into two clusters, with few adults between 40 and 60 years. "
        "The age histogram is in `outputs/figures/age_distribution.png`.",
        "",
        "## Measurement",
        "",
        "Recordings are 60 s at 100 Hz and were already smoothed by the source study with a 10 Hz, "
        "4th order, zero-lag Butterworth filter. This analysis does not filter them again. "
        "Stored COP is in centimeters. Anterior is positive on COPx and right is positive on COPy, "
        "using the source coordinate system. Resultant mean velocity is the COP path length divided by "
        "the elapsed time from the first to the last sample, (6000 - 1) / 100 = 59.99 s. "
        "It is a speed: each step contributes its length, not a signed direction. "
        "Axis mean velocities use the absolute step on that axis. "
        "The area is the 95% prediction ellipse of the COP cloud, using the unbiased covariance and "
        "the finite-sample F critical value. It is not a confidence ellipse for the mean COP.",
        "",
        "The stored COP was checked against COPx = -My / Fz and COPy = Mx / Fz, converted from meters to centimeters. "
        f"Among included trials, the largest median absolute reconstruction error was {recon_text}. "
        f"Mean vertical force divided by body weight (mass times 9.80665 m/s^2) ranged from "
        f"{_num(quality['fz_ratio_min'], 3)} to {_num(quality['fz_ratio_max'], 3)}. "
        f"The largest sample-to-sample COP step among included trials was {_num(quality['max_step_max_cm'], 3)} cm "
        "(the exclusion threshold was 2 cm). "
        f"Included resultant velocities ranged from {_num(quality['speed_min_cm_s'], 2)} to {_num(quality['speed_max_cm_s'], 2)} cm/s. "
        f"Channel checksum failures: {quality['n_checksum_fail']}. "
        f"Header subject-id mismatches: {quality['n_subject_id_mismatch']}. "
        f"Header disagreements beyond 0.2 units for age, height, and mass: "
        f"{quality['n_age_header_mismatch']}, {quality['n_height_header_mismatch']}, and {quality['n_weight_header_mismatch']}.",
        "",
        "## Primary result",
        "",
        f"Closing the eyes increased resultant mean velocity by {_ci(primary, unit='cm/s')} more on foam "
        f"than on the firm surface ({_p(primary['perm_p'])}; "
        f"{int(primary['n_positive'])} of {int(primary['n_subjects'])} participants had a positive interaction). "
        f"The median interaction was {_num(primary['median'])} cm/s "
        f"(95% CI {_num(primary['median_ci_low'])} to {_num(primary['median_ci_high'])}). "
        f"The standardized mean contrast was dz = {_num(primary['dz'])} "
        "(mean divided by the standard deviation of the participant-level contrasts). "
        f"Skewness of those contrasts was {_num(primary['skewness'])}.",
        "",
        "The four simple effects, in cm/s, are the within-person changes named in the table. "
        "Positive values mean more sway in the more demanding condition. "
        "Closing the eyes on the firm surface is a small increase next to the foam effect. "
        f"With eyes open, foam minus firm was positive in {int(_pick(result.contrast_summary, 'mv_cm_s', 'surface_eyes_open')['n_positive'])} "
        f"of {int(_pick(result.contrast_summary, 'mv_cm_s', 'surface_eyes_open')['n_subjects'])} participants.",
        "",
        _contrast_table(result.contrast_summary, "mv_cm_s", "cm/s"),
        "",
        "Participant-level condition means, with bootstrap intervals for the mean:",
        "",
        _condition_table(result.descriptive, "mv_cm_s", "All"),
        "",
        f"On the firm surface with eyes open, the mean of the participant-level velocities was {_ci(firm_open, unit='cm/s')}. "
        f"On foam with eyes closed it was {_ci(foam_closed, unit='cm/s')}. "
        "Figures: `outputs/figures/condition_means.png`, `outputs/figures/forest_mean_velocity.png`, "
        "and `outputs/figures/interaction_distribution.png`.",
        "",
        "On the log scale, a trial-level model with subject-clustered standard errors gives multiplicative versions "
        "of the same contrasts. The interaction is the eyes-closed ratio on foam divided by the eyes-closed ratio "
        f"on the firm surface: {_num(log_interaction['ratio'], 3)} "
        f"(95% CI {_num(log_interaction['ratio_ci_low'], 3)} to {_num(log_interaction['ratio_ci_high'], 3)}). "
        "A ratio above 1 means the proportional increase from closing the eyes is larger on foam. "
        "This is a supporting scale, not a replacement for the cm/s estimand.",
        "",
        "## Age",
        "",
        "Age comparisons use the same participant-level contrasts. "
        "The estimate is the older-group mean minus the younger-group mean. "
        "The bootstrap resamples within each age group. The p value is a two-sided label permutation.",
        "",
        _age_table(result.age_summary, "mv_cm_s", "cm/s"),
        "",
        "Older participants had a larger foam-minus-firm increase, and the interval for that age difference lies above zero with eyes open and with eyes closed. "
        "The intervals for the age difference in the eyes-closed effects, and in the interaction, include zero. "
        "Absolute levels are higher in the older group in every condition, especially on foam. "
        "Those levels compare different people. The foam contrast compares conditions inside the same person, then compares that within-person change between age groups.",
        "",
        f"The interaction changed by {_ci(slope, estimate_key='slope_per_year', digits=3, unit='cm/s per year')} "
        "when age was entered in years instead of the binary source group. "
        "Because few participants are between 40 and 60 years, that slope mostly contrasts the two age clusters. "
        "It is not evidence of a smooth year-by-year change. "
        "See `outputs/figures/interaction_vs_age.png` and `outputs/figures/forest_age_differences.png`.",
        "",
        "Condition means by age group:",
        "",
        "Younger than 60 years",
        "",
        _condition_table(result.descriptive, "mv_cm_s", "Young"),
        "",
        "60 years or older",
        "",
        _condition_table(result.descriptive, "mv_cm_s", "Old"),
        "",
        "In the three-way log model, the age term of interest is the older-minus-younger difference in the log interaction. "
        f"Its multiplicative form was {_num(log_age['ratio'], 3)} "
        f"(cluster-robust 95% CI {_num(log_age['ratio_ci_low'], 3)} to {_num(log_age['ratio_ci_high'], 3)}). "
        "A value above 1 means a larger proportional interaction in the older group. "
        "A value below 1 means a smaller proportional interaction. "
        "That can happen when the absolute vision effect is similar and foam velocity is higher, because a ratio divides by a larger number. "
        "It is not the same estimand as the cm/s age contrast. "
        "The reference coding also makes the lower-order log interaction in that model specific to the younger group, "
        "so the cm/s table above remains the absolute age comparison to read.",
        "",
        "## Direction and sway area",
        "",
        "These are secondary outcomes. Intervals are not adjusted across outcomes.",
        "",
        *secondary_lines,
        "",
        "The axis forest is `outputs/figures/forest_axes.png`. "
        "The area forest is `outputs/figures/forest_ellipse.png`. "
        "The full decomposition is `outputs/tables/contrasts.csv`.",
        "",
        "One unlabeled stabilogram, from the participant whose firm, eyes-open velocity is nearest the sample median, "
        "is in `outputs/figures/example_stabilogram.png`. "
        "The four panels use the same scale and show demeaned COP. "
        "It is an illustration of the signal, not a summary of the sample. "
        "The figure does not carry an identifier, age, or sex.",
        "",
        "## Clustering, repetition, and reliability",
        "",
        "The interaction point estimate from the mean of participant contrasts was "
        f"{_num(validation['interaction_subject_mean'])} cm/s. "
        f"Ordinary least squares on the participant-by-condition means gave {_num(validation['interaction_subject_ols'])} cm/s "
        f"(absolute difference {_num(estimate_gap, 4)} cm/s). "
        f"Ordinary least squares on the trials gave {_num(validation['interaction_trial_ols'])} cm/s "
        f"(absolute difference from the participant mean {_num(trial_gap, 4)} cm/s). "
        "The point estimates agree because the design is essentially balanced. The standard errors do not.",
        "",
        f"The standard deviation of the {n_people} participant-level interaction contrasts was "
        f"{_num(validation['contrast_sd'], 3)} cm/s. "
        f"Divided by the square root of {n_people}, the standard error is {_num(validation['se_participants'], 3)} cm/s. "
        f"Divided by the square root of {quality['n_analytic_trials']:,} trials, the same spread would give "
        f"{_num(validation['se_if_trials_counted_as_people'], 3)} cm/s. "
        "That second number keeps the within-person spread and then pretends each trial is an extra person. It is too small.",
        "",
        f"A different mistake leaves between-person differences in the residual. "
        f"Ordinary least squares on the trials gave an interaction standard error of {_num(validation['se_trial_naive'], 3)} cm/s. "
        f"The same fit with a subject-clustered variance estimate gave {_num(validation['se_trial_cluster'], 3)} cm/s. "
        f"On the participant-by-condition means, the ordinary standard error was {_num(validation['se_subject_naive'], 3)} cm/s "
        f"and the clustered standard error was {_num(validation['se_subject_cluster'], 3)} cm/s. "
        f"The bootstrap standard error was {_num(validation['se_bootstrap'], 3)} cm/s. "
        "The clustered and bootstrap errors agree with the participant-level calculation. "
        "The ordinary residual error does not, because stable differences between people are not uncertainty about a within-person contrast. "
        "The full comparison is `outputs/tables/model_comparison.csv`.",
        "",
        f"The paired t interval for the interaction was {_num(validation['t_ci_low'])} to {_num(validation['t_ci_high'])} cm/s. "
        f"The percentile bootstrap interval was {_num(validation['boot_ci_low'])} to {_num(validation['boot_ci_high'])} cm/s. "
        f"The largest absolute endpoint difference was {_num(t_gap, 3)} cm/s. "
        "The bootstrap interval is the one reported above.",
        "",
        icc_sentence,
        "",
        "Within a condition, the one-way random ICC of resultant mean velocity "
        f"ranged from {_num(icc_min)} to {_num(icc_max)}. "
        f"The within-participant trial SD (SEM) ranged from {_num(sem_min)} to {_num(sem_max)} cm/s. "
        "Averaging the repetitions reduces that trial noise. The ICC table is `outputs/tables/reliability.csv`.",
        "",
        "Ordering the kept trials by file number within each participant and condition, "
        "the cluster-robust change in resultant mean velocity per later repetition was "
        f"{_num(result.repetition['estimate'])} cm/s "
        f"(95% CI {_num(result.repetition['ci_low'])} to {_num(result.repetition['ci_high'])}, "
        f"cluster-robust {_p(result.repetition['p'])}). "
        "Later repetitions were slightly slower. "
        "Every analyzed condition has the same three repetition indexes, so this common drift does not create the vision or surface contrasts.",
        "",
        "## Sensitivity",
        "",
        f"Excluding participants with the source disability flag left {int(disability['n_subjects'])} people. "
        f"The interaction was {_ci(disability, unit='cm/s')}, {_p(disability['perm_p'])}.",
        "",
        f"Dividing each participant's condition means by foot length, and dropping {int(sample_all['n_missing_foot'])} "
        f"analytic participants with missing foot length, left {int(foot['n_subjects'])} people. "
        f"The interaction was {_ci(foot, digits=4, unit='per second')}, {_p(foot['perm_p'])}. "
        "Foot length is constant within a person, so this checks whether the cm/s interaction is an artifact of leaving "
        "body size in the unit. The age comparison of absolute levels can still be influenced by height. "
        f"Mean height was {_num(sample_young['height_cm_mean'], 1)} cm in the younger analytic group and "
        f"{_num(sample_old['height_cm_mean'], 1)} cm in the older analytic group. "
        f"Mean foot length was {_num(sample_young['foot_len_cm_mean'], 1)} cm and {_num(sample_old['foot_len_cm_mean'], 1)} cm. "
        "Dividing by foot length does not remove the age difference in the foam effect. "
        "Older minus younger, eyes open, was "
        f"{_ci(_pick(result.age_summary, 'mv_per_foot_length', 'surface_eyes_open'), estimate_key='diff_old_minus_young', digits=4, unit='per second')}. "
        "The same contrast with eyes closed was "
        f"{_ci(_pick(result.age_summary, 'mv_per_foot_length', 'surface_eyes_closed'), estimate_key='diff_old_minus_young', digits=4, unit='per second')}. "
        "Foot length is only a partial stand-in for body size. Height differs more than foot length between the age groups.",
        "",
        "## Validation",
        "",
        "- WFDB format 32 was read as multiplexed little-endian integers and converted with (digital - baseline) / gain.",
        "- Every included channel checksum matched the header, and the first sample matched the header initial value, "
        f"with {quality['n_checksum_fail']} checksum failures in the whole set.",
        "- Stored COP matched the source moment formulas to the reconstruction error quoted above.",
        "- Header subject, age, height, and mass were compared with BDSinfo. Disagreement counts are quoted above.",
        "- The interaction from participant means agreed with saturated ordinary least squares on the same means.",
        "- Naive and clustered standard errors were computed on the same design matrix so the cost of ignoring clustering is numerical, not rhetorical.",
        "- Unit tests cover path-length velocity, the prediction-ellipse formula, quality thresholds, the interaction algebra, "
        "the sign-flip correction, metadata column restriction, and a synthetic four-condition study.",
        f"- Bootstrap replicates: {result.fingerprint['n_bootstrap']:,}. "
        f"Permutation replicates: {result.fingerprint['n_permutation']:,}. "
        f"Master seed: {result.fingerprint['seed']}. "
        "Each estimand uses a deterministic stream derived from that seed.",
        "",
        "## Limitations",
        "",
        "- The sample is a convenience sample from one laboratory and one examiner. It is mostly women, especially in the older group. "
        "The estimates are not normative reference values and they are not athlete-specific.",
        "- Five recruited participants, most of them in the older group, did not finish every condition. "
        "The source paper attributes those gaps to an inability to complete 60 s. "
        "If those participants would have shown larger increases, the complete-case contrasts understate the increases "
        "in the full recruited sample. Missing trials were not imputed.",
        "- The primary analysis keeps participants with the source disability flag, because the question is about within-person "
        "sensory changes in the recorded cohort. Removing them is the sensitivity analysis above. Disability type is not analyzed.",
        "- Quiet-stance COP velocity is not center-of-mass control, and it is not balance during gait, sport, or a perturbation. "
        "Feet were barefoot, about 10 cm between the heels, with about 20 degrees of toe-out, arms at the sides. "
        "Foam was one 6 cm Airex pad. The results do not transfer to other stances or surfaces by themselves.",
        "- The platform calibration was the factory calibration. Santos and Duarte note that it was not rechecked after installation.",
        "- Signals above 10 Hz are not in the released series. A second filter was not applied.",
        "- The age contrast is between people. Cohort, sex balance, height, activity, and health can differ between the age groups. "
        "Those differences do not confound the within-person vision and surface contrasts. They can confound the comparison of those contrasts across age.",
        "- The age distribution is bimodal. A linear age slope mostly restates the two-group contrast.",
        "- Secondary outcomes and the age models are not a multiplicity-adjusted family. "
        "The pre-specified primary estimand is the resultant-velocity interaction.",
        "- Bootstrap intervals and permutation tests take the recruited participants as the resampling units. They do not remove selection bias.",
        "",
        "## Data, license, and citation",
        "",
        "Contains information from the Human Balance Evaluation Database, version 1.0.0 "
        "(https://physionet.org/content/hbedb/1.0.0/), which is made available under the ODC Attribution License "
        "(https://opendatacommons.org/licenses/by/1.0/).",
        "",
        "The PhysioNet license page for this version, as used for this analysis, is the Open Data Commons Attribution License v1.0. "
        "The 2016 PeerJ article instead says that the PhysioNet copy was released under the ODC Public Domain Dedication and License v1.0. "
        "Those statements disagree. This project follows the license text served with the PhysioNet record and does not redistribute raw recordings or BDSinfo. "
        "Raw recordings and BDSinfo stay in the local `data/` directory, which git ignores. "
        f"SHA-256 of the local BDSinfo.txt: `{result.fingerprint['bdsinfo_sha256']}`. "
        f"SHA-256 of RECORDS: `{result.fingerprint['records_sha256']}`.",
        "",
        "BDSinfo contains illness, medication, disability descriptions, skin color, nationality, and other interview fields. "
        "This analysis does not read those fields into the result tables, figures, or this summary. "
        "The disability flag is kept only as yes or no for the sensitivity analysis.",
        "",
        "Cite the data paper and the database:",
        "",
        "Santos DA, Duarte M. A public data set of human balance evaluations. PeerJ. 2016;4:e2648. https://doi.org/10.7717/peerj.2648",
        "",
        "Santos DA, Duarte M. Human Balance Evaluation Database (version 1.0.0). PhysioNet. 2016. https://doi.org/10.13026/C2WW2W",
        "",
        "Santos DA, Duarte M. A public data set of human balance evaluations. PeerJ Preprints. "
        "Posted 24 June 2016. https://doi.org/10.7287/peerj.preprints.2162v1",
        "",
        "The PhysioNet record also asks for the platform citation. Initials and the issue number follow the DOI record:",
        "",
        "Pollard T, Moody BE, Lehman LH, Gow BJ, Fernandes C, Xie C, Johnson A, Mark RG, Heldt T. "
        "PhysioNet as a global platform for biomedical research. Nature Health. 2026;1(8):792-795. "
        "https://doi.org/10.1038/s44360-026-00096-z",
        "",
        "The data paper cites the earlier platform paper as well:",
        "",
        "Goldberger AL, Amaral LAN, Glass L, Hausdorff JM, Ivanov PC, Mark RG, Mietus JE, Moody GB, Peng C-K, Stanley HE. "
        "PhysioBank, PhysioToolkit, and PhysioNet: components of a new research resource for complex physiologic signals. "
        "Circulation. 2000;101(23):e215-e220. https://doi.org/10.1161/01.CIR.101.23.e215",
        "",
        "Measurement definitions follow Prieto and colleagues (1996) and Duarte and Freitas (2010). "
        "The distinction between a prediction ellipse and a confidence ellipse for the mean follows Duarte (2015).",
        "",
        "Prieto TE, Myklebust JB, Hoffmann RG, Lovett EG, Myklebust BM. Measures of postural steadiness: "
        "differences between healthy young and elderly adults. IEEE Transactions on Biomedical Engineering. "
        "1996;43(9):956-966. https://doi.org/10.1109/10.532130",
        "",
        "Duarte M, Freitas SMSF. Revision of posturography based on force plate for balance evaluation. "
        "Brazilian Journal of Physical Therapy. 2010;14(3):183-192. https://doi.org/10.1590/S1413-35552010000300003",
        "",
        "Duarte M. Comments on \"Ellipse area calculations and their applicability in posturography\" "
        "(Schubert and Kirchner, vol. 39, pages 518-522, 2014). Gait & Posture. 2015;41(1):44-45. "
        "https://doi.org/10.1016/j.gaitpost.2014.08.008",
        "",
        "The original writing, code, tests, and figure design in this project are under CC BY 4.0. "
        "See `LICENSE`. That license does not relicense the Human Balance Evaluation Database.",
        "",
        f"Generated {result.generated_at}. "
        f"Python {result.versions['python']}, numpy {result.versions['numpy']}, "
        f"scipy {result.versions['scipy']}, pandas {result.versions['pandas']}, "
        f"statsmodels {result.versions['statsmodels']}, matplotlib {result.versions['matplotlib']}.",
        "",
    ]
    text = "\n".join(lines)
    assert_plain_prose(text)
    return text


def write_results(result, path: Path) -> str:
    text = render_results(result)
    path = Path(path)
    path.write_text(text, encoding="utf-8")
    return text
