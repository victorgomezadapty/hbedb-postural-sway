"""Participant-level contrasts, not trial-level sample size."""

import numpy as np
import pandas as pd

from hbedb_sway.design import (
    assert_export_frame,
    contrast_frame,
    load_metadata,
    sample_description,
    subject_condition_means,
)
from hbedb_sway.inference import (
    factorial_contrast_table,
    fit_factorial,
    signflip_p,
    summarize_age_differences,
    summarize_contrasts,
)


def _condition_rows(subject, speeds, age_group, age, sex="F", disability=False, foot=24.0):
    rows = []
    for (vision, surface), speed in speeds.items():
        for rep in range(3):
            rows.append(
                {
                    "trial": f"T{subject}{vision[0]}{surface[0]}{rep}",
                    "subject": subject,
                    "vision": vision,
                    "surface": surface,
                    "age_years": age,
                    "age_group": age_group,
                    "sex": sex,
                    "height_cm": 170.0,
                    "weight_kg": 70.0,
                    "bmi": 24.0,
                    "foot_len_cm": foot,
                    "self_reported_disability": disability,
                    "exclude": False,
                    "mv_cm_s": speed,
                    "mv_ap_cm_s": speed / 2,
                    "mv_ml_cm_s": speed / 2,
                    "ellipse_cm2": speed,
                }
            )
    return rows


def _speeds(firm_open, firm_closed, foam_open, foam_closed):
    return {
        ("Open", "Firm"): firm_open,
        ("Closed", "Firm"): firm_closed,
        ("Open", "Foam"): foam_open,
        ("Closed", "Foam"): foam_closed,
    }


def _study():
    rows = []
    # Two identical younger participants, interaction = (5 - 3) - (2 - 1) = 1.
    for subject in (1, 2):
        rows.extend(_condition_rows(subject, _speeds(1, 2, 3, 5), "Young", 30))
    # Two identical older participants, interaction = (8 - 3) - (2 - 1) = 4.
    for subject in (3, 4):
        rows.extend(_condition_rows(subject, _speeds(1, 2, 3, 8), "Old", 70, sex="M"))
    # One incomplete participant must not become five people, or one extra person.
    rows.extend(_condition_rows(5, {("Open", "Firm"): 1, ("Closed", "Firm"): 2}, "Old", 75))
    return pd.DataFrame(rows)


def test_twelve_trials_from_one_person_count_as_one_person():
    trials = _study()
    means = subject_condition_means(trials)
    assert means["subject"].nunique() == 5
    frame = contrast_frame(means, "mv_cm_s")
    assert len(frame) == 4
    assert set(frame["subject"]) == {1, 2, 3, 4}
    summary = summarize_contrasts(frame, "mv_cm_s", n_boot=400, n_perm=500, seed=2648)
    interaction = summary[summary["contrast"] == "interaction"].iloc[0]
    assert interaction["n_subjects"] == 4
    assert abs(interaction["mean"] - 2.5) < 1e-12
    young = frame[frame["age_group"] == "Young"]["interaction"]
    old = frame[frame["age_group"] == "Old"]["interaction"]
    assert np.allclose(young, 1.0)
    assert np.allclose(old, 4.0)
    age = summarize_age_differences(frame, "mv_cm_s", n_boot=400, n_perm=500, seed=2648)
    age_interaction = age[age["contrast"] == "interaction"].iloc[0]
    assert abs(age_interaction["diff_old_minus_young"] - 3.0) < 1e-12
    description = sample_description(frame)
    assert int(description.loc[description["group"] == "All", "n"].iloc[0]) == 4


def test_signflip_of_a_zero_mean_symmetric_sample_is_not_small():
    p_zero = signflip_p(np.zeros(12), n_perm=1000, seed=1)
    assert p_zero == 1.0
    p_shift = signflip_p(np.ones(12), n_perm=2000, seed=2)
    assert p_shift < 0.01


def test_metadata_reader_drops_health_narrative(tmp_path):
    path = tmp_path / "BDSinfo.txt"
    header = (
        "Trial\tSubject\tVision\tSurface\tAge\tAgeGroup\tGender\tHeight\tWeight\tBMI\t"
        "FootLen\tDisability\tIllness\tMedication\n"
    )
    row = "BDS00001\t1\tOpen\tFirm\t33\tYoung\tF\t160\t60\t23.4\t24\tNo\tSecret illness\tSecret drug\n"
    path.write_text(header + row, encoding="utf-8")
    loaded = load_metadata(path)
    assert "Illness" not in loaded.columns
    assert "illness" not in loaded.columns
    assert "Medication" not in loaded.columns
    assert loaded.loc[0, "self_reported_disability"] == False  # noqa: E712
    frame = loaded.copy()
    frame["Illness"] = "should fail"
    try:
        assert_export_frame(frame)
    except RuntimeError:
        return
    raise AssertionError("A health-narrative column was exported.")


def test_young_label_cannot_hide_an_older_age(tmp_path):
    path = tmp_path / "BDSinfo.txt"
    header = (
        "Trial\tSubject\tVision\tSurface\tAge\tAgeGroup\tGender\tHeight\tWeight\tBMI\tFootLen\tDisability\n"
    )
    row = "BDS00001\t1\tOpen\tFirm\t65\tYoung\tF\t160\t60\t23.4\t24\tNo\n"
    path.write_text(header + row, encoding="utf-8")
    try:
        load_metadata(path)
    except ValueError:
        return
    raise AssertionError("An inconsistent age label was accepted.")


def test_clustered_standard_error_exceeds_the_naive_error_when_people_differ():
    rng = np.random.default_rng(2648)
    rows = []
    effects = {
        ("Open", "Firm"): 0.0,
        ("Closed", "Firm"): 1.0,
        ("Open", "Foam"): 2.0,
        ("Closed", "Foam"): 6.0,
    }
    for subject in range(30):
        intercept = float(rng.normal(0.0, 4.0))
        for (vision, surface), effect in effects.items():
            for _rep in range(3):
                rows.append(
                    {
                        "subject": subject,
                        "vision": vision,
                        "surface": surface,
                        "mv_cm_s": effect + intercept + float(rng.normal(0.0, 0.25)),
                    }
                )
    frame = pd.DataFrame(rows)
    naive, clustered, _data = fit_factorial(frame, "mv_cm_s")
    table = factorial_contrast_table(naive, clustered)
    interaction = table[table["contrast"] == "interaction"].iloc[0]
    assert abs(interaction["estimate"] - 3.0) < 0.15
    # Between-person intercepts inflate the ordinary residual, so the naive SE
    # of this within-person interaction is too large. The clustered SE is not.
    assert interaction["se_naive"] > interaction["se_cluster"] * 2
