# Vision, support surface, and age in quiet-stance postural sway

Analysis by Víctor Andrés Gómez López.

Reproducible analysis of the Human Balance Evaluation Database. This publication contains derived participant-level results, analysis code, tests, figures, and the executed notebook. Raw recordings and BDSinfo are excluded and downloaded locally when reproducing the analysis.

The original writing, code, tests, and figure design in this project are licensed under CC BY 4.0. See `LICENSE`. That license does not relicense the database.

## Question

In the adults who completed every condition, how does quiet-stance center-of-pressure mean velocity change when vision is removed and when a firm surface is replaced by foam? Is the effect of closing the eyes larger on foam than on the firm surface? As a secondary question, do those within-person changes differ between the source age groups (younger than 60 years, and 60 years or older)?

The primary estimand is that interaction for resultant mean velocity, in cm/s. One participant contributes one number, regardless of how many trials that person performed. The analysis does not support a treatment claim, a diagnostic cutoff, or a coaching prescription.

## Data

Human Balance Evaluation Database, version 1.0.0.

- https://physionet.org/content/hbedb/1.0.0/
- DOI: https://doi.org/10.13026/C2WW2W
- License page used here: Open Data Commons Attribution License v1.0

See `DATA_LICENSE.md` for attribution and the distinction between the database license and this analysis license. The 2016 PeerJ article describes the PhysioNet copy as ODC-PDDL. The license page served with version 1.0.0 is ODC-BY. This project follows the page served with the files.

Scientific citation for the data paper and the database:

Santos DA, Duarte M. A public data set of human balance evaluations. PeerJ. 2016;4:e2648. https://doi.org/10.7717/peerj.2648

Santos DA, Duarte M. Human Balance Evaluation Database (version 1.0.0). PhysioNet. 2016. https://doi.org/10.13026/C2WW2W

The preprint DOI record uses the same paper title: https://doi.org/10.7287/peerj.preprints.2162v1. The PhysioNet landing page has also printed that preprint as "A Public Database of Human Balance Evaluations." Full platform and methods citations are in `RESULTS.md` and `DATA_LICENSE.md`.

## Reproduce

Python 3.12 was used for this analysis. From the project root:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install -e .
.venv/bin/python scripts/download_hbedb.py
.venv/bin/python -m pytest
.venv/bin/python scripts/run_analysis.py
.venv/bin/python -m jupyter nbconvert --to notebook --execute --inplace notebooks/vision_surface_postural_sway.ipynb
```

`make install`, `make download`, `make test`, `make analysis`, and `make notebook` are the same steps. The download is about 360 MB and goes to `data/raw/`. The analysis reads every recording once, writes tables and figures under `outputs/`, and rewrites `RESULTS.md`.

## What the code does

Trials are 60 s at 100 Hz, already filtered at 10 Hz by the source study. Eight channels give force in newtons, moment in newton meters, and COP in centimeters. This analysis uses the stored COP and checks it against the source formulas, COPx = -My / Fz and COPy = Mx / Fz.

Resultant mean velocity is path length divided by 59.99 s. The area is the 95% prediction ellipse of the COP cloud, not a confidence ellipse of the mean.

Quality screens are file integrity, vertical force against body weight, COP reconstruction, a 2 cm sample-to-sample step, a 25 cm range, and a speed outside 0.05 to 20 cm/s. They are not tuned on the vision or surface coefficients.

Participants with all four conditions enter the primary analysis. Repetitions are averaged within person and condition. Uncertainty is a percentile bootstrap and a sign-flip test over participants (10,000 bootstrap draws, 20,000 permutations, seed 2648). A trial-level regression is reported only with subject-clustered standard errors, next to the naive standard error that ignores clustering.

Age uses the source labels: Young means under 60 years, and Old means 60 years or older. Health narratives in BDSinfo are not read into the outputs. A yes or no disability flag is used only in a sensitivity analysis.

## Layout

- `src/hbedb_sway/`: download, WFDB reader, metrics, quality screens, contrasts, uncertainty, figures, and the results text
- `scripts/download_hbedb.py`: documented downloader
- `scripts/run_analysis.py`: full run
- `tests/`: formula, design, clustering, and file checks
- `notebooks/vision_surface_postural_sway.ipynb`: executed narrative
- `RESULTS.md`: numerical summary
- `DATA_LICENSE.md`: license caveat and citations
- `outputs/`: tables and figures produced by the run

## Limitations

The sample is a convenience sample from one laboratory, mostly women, with a bimodal age distribution. Five participants did not finish the harder conditions. COP velocity in quiet stance is not balance in sport or in a clinical test of treatment. Details and the numerical results are in `RESULTS.md`.

## Main result

In 158 participants with all four conditions, closing the eyes added 0.65 cm/s more resultant mean COP velocity on foam than on the firm surface (95% bootstrap CI 0.56 to 0.75, sign-flip p < 0.001). Age differences are secondary and exploratory. This observational analysis is not a diagnostic tool, a treatment effect, or a coaching recommendation.

## Research outputs

All figures, summary tables, participant-level condition means, and the full numerical report are included under `outputs/` and `RESULTS.md`. This repository and its Kaggle companion exclude the source `.dat` and `.hea` recordings and the BDSinfo interview file.

- Case study: https://victor-gomez-portfolio.vercel.app/projects/hbedb-postural-sway
- Kaggle derived outputs: https://www.kaggle.com/datasets/vctorandrsgmezlpez/hbedb-quiet-stance-sway-vision-and-surface
- Source data: https://physionet.org/content/hbedb/1.0.0/

## Cite this analysis

Gómez López, Víctor Andrés. (2026). Vision, support surface, and age in quiet-stance postural sway: analysis of HBEDB v1.0.0. CC BY 4.0 for the analysis code and original writing; the source database retains its own ODC Attribution License.
