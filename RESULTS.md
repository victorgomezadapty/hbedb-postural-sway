# Vision, support surface, and age in quiet-stance postural sway

Analysis by Víctor Andrés Gómez López.

This is an independent analysis of the Human Balance Evaluation Database, version 1.0.0. It estimates how vision and the support surface change quiet-stance center-of-pressure sway, and whether those within-person changes differ between the age groups defined by the source study. It does not estimate a treatment effect, a diagnostic cutoff, or a training recommendation.

## Question

In adults who completed the four quiet-stance conditions, how much does resultant center-of-pressure mean velocity change when the eyes are closed and when a firm surface is replaced by foam, and is the effect of closing the eyes larger on foam than on the firm surface? The secondary question is whether those within-person changes differ between adults younger than 60 years and adults aged 60 years or older, which is the age grouping supplied with the database.

The primary estimand is the interaction for resultant mean velocity, in cm/s. It equals the eyes-closed minus eyes-open difference on foam, minus the same difference on the firm surface. A positive value means that closing the eyes adds more velocity on foam than on the firm surface. The four simple effects are the planned decomposition of that interaction, not a separate family of primary tests. Anteroposterior velocity, mediolateral velocity, and the 95% prediction ellipse area are secondary outcomes. Age comparisons are secondary.

## Sample and unit of analysis

The database contains 1,930 stored trials from 163 participants. A complete protocol is 12 trials: three repetitions of each of four conditions. There were 5 participants without all four conditions (1 in the younger group and 4 in the older group). Absent condition cells, counting participants, were foam with eyes closed (5), foam with eyes open (3). Santos and Duarte (2016) state that these trials are missing because the participant could not complete 60 s. The primary contrasts use only participants with at least one valid trial in every condition, which is 158 people and 1,896 trials. Quality control excluded no trials. Every analytic participant had three valid repetitions in every condition. Each participant then contributes the mean of the available repetitions in that condition. Every interval below resamples or clusters those participants. The 1,930 trials are not treated as 1,930 independent people.

| Group | n | Female | Male | Age range (years) | Median age | Mean height (cm) | Mean mass (kg) | Disability flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| All analytic participants | 158 | 114 | 44 | 18.3 to 85.8 | 39.8 | 162.5 | 62.2 | 12 |
| Younger than 60 years | 86 | 56 | 30 | 18.3 to 59.0 | 25.5 | 166.7 | 61.5 | 3 |
| 60 years or older | 72 | 58 | 14 | 60.5 to 85.8 | 71.8 | 157.4 | 63.0 | 9 |

The analytic sample has 114 women and 44 men. The older group has 58 women and 14 men, so the age comparison is not balanced by sex. 12 analytic participants have the source disability flag (Disability = Yes in BDSinfo; the free-text description is not used or shown). Ages run from 18.3 to 59.0 years in the younger group and from 60.5 to 85.8 years in the older group. The source paper notes that the ages fall mainly into two clusters, with few adults between 40 and 60 years. The age histogram is in `outputs/figures/age_distribution.png`.

## Measurement

Recordings are 60 s at 100 Hz and were already smoothed by the source study with a 10 Hz, 4th order, zero-lag Butterworth filter. This analysis does not filter them again. Stored COP is in centimeters. Anterior is positive on COPx and right is positive on COPy, using the source coordinate system. Resultant mean velocity is the COP path length divided by the elapsed time from the first to the last sample, (6000 - 1) / 100 = 59.99 s. It is a speed: each step contributes its length, not a signed direction. Axis mean velocities use the absolute step on that axis. The area is the 95% prediction ellipse of the COP cloud, using the unbiased covariance and the finite-sample F critical value. It is not a confidence ellipse for the mean COP.

The stored COP was checked against COPx = -My / Fz and COPy = Mx / Fz, converted from meters to centimeters. Among included trials, the largest median absolute reconstruction error was 2.61e-07 cm. Mean vertical force divided by body weight (mass times 9.80665 m/s^2) ranged from 0.950 to 1.037. The largest sample-to-sample COP step among included trials was 1.400 cm (the exclusion threshold was 2 cm). Included resultant velocities ranged from 0.40 to 10.18 cm/s. Channel checksum failures: 0. Header subject-id mismatches: 0. Header disagreements beyond 0.2 units for age, height, and mass: 0, 0, and 0.

## Primary result

Closing the eyes increased resultant mean velocity by 0.65 cm/s (95% CI 0.56 to 0.75) more on foam than on the firm surface (p < 0.001; 145 of 158 participants had a positive interaction). The median interaction was 0.60 cm/s (95% CI 0.48 to 0.67). The standardized mean contrast was dz = 1.08 (mean divided by the standard deviation of the participant-level contrasts). Skewness of those contrasts was 0.30.

The four simple effects, in cm/s, are the within-person changes named in the table. Positive values mean more sway in the more demanding condition. Closing the eyes on the firm surface is a small increase next to the foam effect. With eyes open, foam minus firm was positive in 158 of 158 participants.

| Contrast | Mean (cm/s) | 95% CI | Median | Positive contrasts | Sign-flip p |
| --- | --- | --- | --- | --- | --- |
| Eyes closed minus eyes open, firm surface | 0.10 | 0.06 to 0.14 | 0.07 | 109 of 158 | p < 0.001 |
| Eyes closed minus eyes open, foam surface | 0.75 | 0.66 to 0.85 | 0.63 | 146 of 158 | p < 0.001 |
| Foam minus firm, eyes open | 1.96 | 1.84 to 2.08 | 1.81 | 158 of 158 | p < 0.001 |
| Foam minus firm, eyes closed | 2.61 | 2.47 to 2.76 | 2.48 | 158 of 158 | p < 0.001 |
| Interaction: extra eyes-closed effect on foam | 0.65 | 0.56 to 0.75 | 0.60 | 145 of 158 | p < 0.001 |

Participant-level condition means, with bootstrap intervals for the mean:

| Surface | Vision | n | Mean (cm/s) | 95% CI | Median | IQR |
| --- | --- | --- | --- | --- | --- | --- |
| Firm | Eyes open | 158 | 0.99 | 0.93 to 1.05 | 0.91 | 0.72 to 1.14 |
| Firm | Eyes closed | 158 | 1.09 | 1.02 to 1.17 | 0.99 | 0.75 to 1.27 |
| Foam | Eyes open | 158 | 2.95 | 2.81 to 3.11 | 2.77 | 2.15 to 3.55 |
| Foam | Eyes closed | 158 | 3.71 | 3.52 to 3.90 | 3.53 | 2.85 to 4.29 |

On the firm surface with eyes open, the mean of the participant-level velocities was 0.99 cm/s (95% CI 0.93 to 1.05). On foam with eyes closed it was 3.71 cm/s (95% CI 3.52 to 3.90). Figures: `outputs/figures/condition_means.png`, `outputs/figures/forest_mean_velocity.png`, and `outputs/figures/interaction_distribution.png`.

On the log scale, a trial-level model with subject-clustered standard errors gives multiplicative versions of the same contrasts. The interaction is the eyes-closed ratio on foam divided by the eyes-closed ratio on the firm surface: 1.156 (95% CI 1.118 to 1.195). A ratio above 1 means the proportional increase from closing the eyes is larger on foam. This is a supporting scale, not a replacement for the cm/s estimand.

## Age

Age comparisons use the same participant-level contrasts. The estimate is the older-group mean minus the younger-group mean. The bootstrap resamples within each age group. The p value is a two-sided label permutation.

| Contrast | Older minus younger (cm/s) | 95% CI | Permutation p |
| --- | --- | --- | --- |
| Eyes closed minus eyes open, firm surface | 0.03 | -0.06 to 0.12 | p = 0.510 |
| Eyes closed minus eyes open, foam surface | -0.03 | -0.23 to 0.18 | p = 0.802 |
| Foam minus firm, eyes open | 1.00 | 0.81 to 1.18 | p < 0.001 |
| Foam minus firm, eyes closed | 0.94 | 0.68 to 1.21 | p < 0.001 |
| Interaction: extra eyes-closed effect on foam | -0.05 | -0.25 to 0.14 | p = 0.572 |

Older participants had a larger foam-minus-firm increase, and the interval for that age difference lies above zero with eyes open and with eyes closed. The intervals for the age difference in the eyes-closed effects, and in the interaction, include zero. Absolute levels are higher in the older group in every condition, especially on foam. Those levels compare different people. The foam contrast compares conditions inside the same person, then compares that within-person change between age groups.

The interaction changed by -0.002 cm/s per year (95% CI -0.007 to 0.003) when age was entered in years instead of the binary source group. Because few participants are between 40 and 60 years, that slope mostly contrasts the two age clusters. It is not evidence of a smooth year-by-year change. See `outputs/figures/interaction_vs_age.png` and `outputs/figures/forest_age_differences.png`.

Condition means by age group:

Younger than 60 years

| Surface | Vision | n | Mean (cm/s) | 95% CI | Median | IQR |
| --- | --- | --- | --- | --- | --- | --- |
| Firm | Eyes open | 86 | 0.88 | 0.81 to 0.94 | 0.81 | 0.66 to 1.04 |
| Firm | Eyes closed | 86 | 0.96 | 0.89 to 1.05 | 0.83 | 0.71 to 1.15 |
| Foam | Eyes open | 86 | 2.38 | 2.24 to 2.55 | 2.22 | 1.94 to 2.63 |
| Foam | Eyes closed | 86 | 3.15 | 2.95 to 3.37 | 2.94 | 2.45 to 3.50 |

60 years or older

| Surface | Vision | n | Mean (cm/s) | 95% CI | Median | IQR |
| --- | --- | --- | --- | --- | --- | --- |
| Firm | Eyes open | 72 | 1.14 | 1.04 to 1.24 | 1.01 | 0.87 to 1.28 |
| Firm | Eyes closed | 72 | 1.25 | 1.13 to 1.38 | 1.12 | 0.93 to 1.42 |
| Foam | Eyes open | 72 | 3.64 | 3.47 to 3.82 | 3.54 | 3.15 to 4.04 |
| Foam | Eyes closed | 72 | 4.38 | 4.14 to 4.65 | 4.23 | 3.70 to 4.85 |

In the three-way log model, the age term of interest is the older-minus-younger difference in the log interaction. Its multiplicative form was 0.912 (cluster-robust 95% CI 0.852 to 0.977). A value above 1 means a larger proportional interaction in the older group. A value below 1 means a smaller proportional interaction. That can happen when the absolute vision effect is similar and foam velocity is higher, because a ratio divides by a larger number. It is not the same estimand as the cm/s age contrast. The reference coding also makes the lower-order log interaction in that model specific to the younger group, so the cm/s table above remains the absolute age comparison to read.

## Direction and sway area

These are secondary outcomes. Intervals are not adjusted across outcomes.

Anteroposterior mean velocity interaction: 0.48 cm/s (95% CI 0.40 to 0.55), p < 0.001.
Mediolateral mean velocity interaction: 0.35 cm/s (95% CI 0.30 to 0.40), p < 0.001.
95% prediction ellipse area interaction: 3.82 cm^2 (95% CI 2.81 to 4.99), p < 0.001.

The axis forest is `outputs/figures/forest_axes.png`. The area forest is `outputs/figures/forest_ellipse.png`. The full decomposition is `outputs/tables/contrasts.csv`.

One unlabeled stabilogram, from the participant whose firm, eyes-open velocity is nearest the sample median, is in `outputs/figures/example_stabilogram.png`. The four panels use the same scale and show demeaned COP. It is an illustration of the signal, not a summary of the sample. The figure does not carry an identifier, age, or sex.

## Clustering, repetition, and reliability

The interaction point estimate from the mean of participant contrasts was 0.65 cm/s. Ordinary least squares on the participant-by-condition means gave 0.65 cm/s (absolute difference 0.0000 cm/s). Ordinary least squares on the trials gave 0.65 cm/s (absolute difference from the participant mean 0.0000 cm/s). The point estimates agree because the design is essentially balanced. The standard errors do not.

The standard deviation of the 158 participant-level interaction contrasts was 0.601 cm/s. Divided by the square root of 158, the standard error is 0.048 cm/s. Divided by the square root of 1,896 trials, the same spread would give 0.014 cm/s. That second number keeps the within-person spread and then pretends each trial is an extra person. It is too small.

A different mistake leaves between-person differences in the residual. Ordinary least squares on the trials gave an interaction standard error of 0.080 cm/s. The same fit with a subject-clustered variance estimate gave 0.048 cm/s. On the participant-by-condition means, the ordinary standard error was 0.134 cm/s and the clustered standard error was 0.048 cm/s. The bootstrap standard error was 0.047 cm/s. The clustered and bootstrap errors agree with the participant-level calculation. The ordinary residual error does not, because stable differences between people are not uncertainty about a within-person contrast. The full comparison is `outputs/tables/model_comparison.csv`.

The paired t interval for the interaction was 0.56 to 0.75 cm/s. The percentile bootstrap interval was 0.56 to 0.75 cm/s. The largest absolute endpoint difference was 0.002 cm/s. The bootstrap interval is the one reported above.

After the four condition means were included, a random-intercept model attributed 60.4% of the remaining variance to stable differences between participants. The fit converged.

Within a condition, the one-way random ICC of resultant mean velocity ranged from 0.79 to 0.91. The within-participant trial SD (SEM) ranged from 0.18 to 0.40 cm/s. Averaging the repetitions reduces that trial noise. The ICC table is `outputs/tables/reliability.csv`.

Ordering the kept trials by file number within each participant and condition, the cluster-robust change in resultant mean velocity per later repetition was -0.10 cm/s (95% CI -0.11 to -0.08, cluster-robust p < 0.001). Later repetitions were slightly slower. Every analyzed condition has the same three repetition indexes, so this common drift does not create the vision or surface contrasts.

## Sensitivity

Excluding participants with the source disability flag left 146 people. The interaction was 0.67 cm/s (95% CI 0.59 to 0.77), p < 0.001.

Dividing each participant's condition means by foot length, and dropping 2 analytic participants with missing foot length, left 156 people. The interaction was 0.0283 per second (95% CI 0.0242 to 0.0324), p < 0.001. Foot length is constant within a person, so this checks whether the cm/s interaction is an artifact of leaving body size in the unit. The age comparison of absolute levels can still be influenced by height. Mean height was 166.7 cm in the younger analytic group and 157.4 cm in the older analytic group. Mean foot length was 23.2 cm and 22.7 cm. Dividing by foot length does not remove the age difference in the foam effect. Older minus younger, eyes open, was 0.0451 per second (95% CI 0.0362 to 0.0543). The same contrast with eyes closed was 0.0431 per second (95% CI 0.0315 to 0.0546). Foot length is only a partial stand-in for body size. Height differs more than foot length between the age groups.

## Validation

- WFDB format 32 was read as multiplexed little-endian integers and converted with (digital - baseline) / gain.
- Every included channel checksum matched the header, and the first sample matched the header initial value, with 0 checksum failures in the whole set.
- Stored COP matched the source moment formulas to the reconstruction error quoted above.
- Header subject, age, height, and mass were compared with BDSinfo. Disagreement counts are quoted above.
- The interaction from participant means agreed with saturated ordinary least squares on the same means.
- Naive and clustered standard errors were computed on the same design matrix so the cost of ignoring clustering is numerical, not rhetorical.
- Unit tests cover path-length velocity, the prediction-ellipse formula, quality thresholds, the interaction algebra, the sign-flip correction, metadata column restriction, and a synthetic four-condition study.
- Bootstrap replicates: 10,000. Permutation replicates: 20,000. Master seed: 2648. Each estimand uses a deterministic stream derived from that seed.

## Limitations

- The sample is a convenience sample from one laboratory and one examiner. It is mostly women, especially in the older group. The estimates are not normative reference values and they are not athlete-specific.
- Five recruited participants, most of them in the older group, did not finish every condition. The source paper attributes those gaps to an inability to complete 60 s. If those participants would have shown larger increases, the complete-case contrasts understate the increases in the full recruited sample. Missing trials were not imputed.
- The primary analysis keeps participants with the source disability flag, because the question is about within-person sensory changes in the recorded cohort. Removing them is the sensitivity analysis above. Disability type is not analyzed.
- Quiet-stance COP velocity is not center-of-mass control, and it is not balance during gait, sport, or a perturbation. Feet were barefoot, about 10 cm between the heels, with about 20 degrees of toe-out, arms at the sides. Foam was one 6 cm Airex pad. The results do not transfer to other stances or surfaces by themselves.
- The platform calibration was the factory calibration. Santos and Duarte note that it was not rechecked after installation.
- Signals above 10 Hz are not in the released series. A second filter was not applied.
- The age contrast is between people. Cohort, sex balance, height, activity, and health can differ between the age groups. Those differences do not confound the within-person vision and surface contrasts. They can confound the comparison of those contrasts across age.
- The age distribution is bimodal. A linear age slope mostly restates the two-group contrast.
- Secondary outcomes and the age models are not a multiplicity-adjusted family. The pre-specified primary estimand is the resultant-velocity interaction.
- Bootstrap intervals and permutation tests take the recruited participants as the resampling units. They do not remove selection bias.

## Data, license, and citation

Contains information from the Human Balance Evaluation Database, version 1.0.0 (https://physionet.org/content/hbedb/1.0.0/), which is made available under the ODC Attribution License (https://opendatacommons.org/licenses/by/1.0/).

The PhysioNet license page for this version, as used for this analysis, is the Open Data Commons Attribution License v1.0. The 2016 PeerJ article instead says that the PhysioNet copy was released under the ODC Public Domain Dedication and License v1.0. Those statements disagree. This project follows the license text served with the PhysioNet record and does not redistribute raw recordings or BDSinfo. Raw recordings and BDSinfo stay in the local `data/` directory, which git ignores. SHA-256 of the local BDSinfo.txt: `012a7124b5f12a6d9be94f5a2bd70f181d6d33c928018ba872540a9c776326a6`. SHA-256 of RECORDS: `b6720632cf8ee58422e742811ad012d638dd0bb232a7048b655665fc17e45914`.

BDSinfo contains illness, medication, disability descriptions, skin color, nationality, and other interview fields. This analysis does not read those fields into the result tables, figures, or this summary. The disability flag is kept only as yes or no for the sensitivity analysis.

Cite the data paper and the database:

Santos DA, Duarte M. A public data set of human balance evaluations. PeerJ. 2016;4:e2648. https://doi.org/10.7717/peerj.2648

Santos DA, Duarte M. Human Balance Evaluation Database (version 1.0.0). PhysioNet. 2016. https://doi.org/10.13026/C2WW2W

Santos DA, Duarte M. A public data set of human balance evaluations. PeerJ Preprints. Posted 24 June 2016. https://doi.org/10.7287/peerj.preprints.2162v1

The PhysioNet record also asks for the platform citation. Initials and the issue number follow the DOI record:

Pollard T, Moody BE, Lehman LH, Gow BJ, Fernandes C, Xie C, Johnson A, Mark RG, Heldt T. PhysioNet as a global platform for biomedical research. Nature Health. 2026;1(8):792-795. https://doi.org/10.1038/s44360-026-00096-z

The data paper cites the earlier platform paper as well:

Goldberger AL, Amaral LAN, Glass L, Hausdorff JM, Ivanov PC, Mark RG, Mietus JE, Moody GB, Peng C-K, Stanley HE. PhysioBank, PhysioToolkit, and PhysioNet: components of a new research resource for complex physiologic signals. Circulation. 2000;101(23):e215-e220. https://doi.org/10.1161/01.CIR.101.23.e215

Measurement definitions follow Prieto and colleagues (1996) and Duarte and Freitas (2010). The distinction between a prediction ellipse and a confidence ellipse for the mean follows Duarte (2015).

Prieto TE, Myklebust JB, Hoffmann RG, Lovett EG, Myklebust BM. Measures of postural steadiness: differences between healthy young and elderly adults. IEEE Transactions on Biomedical Engineering. 1996;43(9):956-966. https://doi.org/10.1109/10.532130

Duarte M, Freitas SMSF. Revision of posturography based on force plate for balance evaluation. Brazilian Journal of Physical Therapy. 2010;14(3):183-192. https://doi.org/10.1590/S1413-35552010000300003

Duarte M. Comments on "Ellipse area calculations and their applicability in posturography" (Schubert and Kirchner, vol. 39, pages 518-522, 2014). Gait & Posture. 2015;41(1):44-45. https://doi.org/10.1016/j.gaitpost.2014.08.008

The original writing, code, tests, and figure design in this project are under CC BY 4.0. See `LICENSE`. That license does not relicense the Human Balance Evaluation Database.

Generated 2026-11-06 09:06 UTC. Python 3.12.3, numpy 2.5.4, scipy 1.18.1, pandas 3.1.1, statsmodels 0.15.0, matplotlib 3.11.2.
