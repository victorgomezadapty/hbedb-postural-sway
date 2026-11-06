"""Dataset identity, license pointers, and pre-specified analysis constants.

Quality thresholds are physical screens for a 60 s barefoot quiet-stance
recording. They were fixed from the protocol and from signal integrity, not
from the vision or surface coefficients.
"""

from __future__ import annotations

DATASET_NAME = "Human Balance Evaluation Database"
DATASET_VERSION = "1.0.0"
DATASET_DOI = "10.13026/C2WW2W"
DATASET_PAGE = "https://physionet.org/content/hbedb/1.0.0/"
DATASET_FILES = "https://physionet.org/files/hbedb/1.0.0/"
DATASET_S3_HTTPS = "https://physionet-open.s3.amazonaws.com/hbedb/1.0.0/"
LICENSE_NAME = "Open Data Commons Attribution License v1.0"
LICENSE_SHORT = "ODC-BY 1.0"
LICENSE_URI = "https://opendatacommons.org/licenses/by/1.0/"
PHYSIONET_LICENSE_PAGE = "https://www.physionet.org/content/hbedb/view-license/1.0.0/"

# The 2016 PeerJ article says the PhysioNet copy used ODC-PDDL. The license
# page served for version 1.0.0 at the time of this analysis is ODC-BY 1.0.
# DATA_LICENSE.md records that discrepancy. This code follows the license
# page that PhysioNet serves with the files.
PAPER_STATED_PHYSIONET_LICENSE = "ODC Public Domain Dedication and License v1.0"
PAPER_STATED_LICENSE_URI = "https://opendatacommons.org/licenses/pddl/1.0/"

FS_HZ = 100.0
N_SAMPLES = 6000
N_CHANNELS = 8
CHANNEL_NAMES = ("Fx", "Fy", "Fz", "Mx", "My", "Mz", "COPx", "COPy")
GRAVITY_MPS2 = 9.80665

FZ_RATIO_MIN = 0.75
FZ_RATIO_MAX = 1.25
FZ_MIN_N = 50.0
COP_RECON_MAX_CM = 0.05
MAX_STEP_CM = 2.0
SPEED_MIN_CM_S = 0.05
SPEED_MAX_CM_S = 20.0
RANGE_MAX_CM = 25.0

BOOTSTRAP_REPLICATES = 10_000
PERMUTATION_REPLICATES = 20_000
RNG_SEED = 2648

# Columns read from BDSinfo. Health narratives, questionnaires, skin color,
# nationality, and the evaluation timestamp are intentionally absent.
KEPT_METADATA = (
    "Trial",
    "Subject",
    "Vision",
    "Surface",
    "Age",
    "AgeGroup",
    "Gender",
    "Height",
    "Weight",
    "BMI",
    "FootLen",
    "Disability",
)

BANNED_EXPORT_COLUMNS = {
    "illness",
    "illness2",
    "medication",
    "nmedication",
    "disability2",
    "skincolor",
    "nationality",
    "footwear",
    "ortho-prosthesis",
    "ortho-prosthesis2",
    "falls12m",
    "date",
}

CONTRASTS = (
    ("vision_on_firm", "Eyes closed minus eyes open, firm surface"),
    ("vision_on_foam", "Eyes closed minus eyes open, foam surface"),
    ("surface_eyes_open", "Foam minus firm, eyes open"),
    ("surface_eyes_closed", "Foam minus firm, eyes closed"),
    ("interaction", "Interaction: extra eyes-closed effect on foam"),
)

PRIMARY_OUTCOME = "mv_cm_s"
PRIMARY_CONTRAST = "interaction"
SECONDARY_OUTCOMES = ("mv_ap_cm_s", "mv_ml_cm_s", "ellipse_cm2")
ALL_OUTCOMES = (PRIMARY_OUTCOME, *SECONDARY_OUTCOMES)

OUTCOME_UNITS = {
    "mv_cm_s": "cm/s",
    "mv_ap_cm_s": "cm/s",
    "mv_ml_cm_s": "cm/s",
    "ellipse_cm2": "cm^2",
    "mv_per_foot_length": "1/s",
}

OUTCOME_LABELS = {
    "mv_cm_s": "Resultant mean velocity",
    "mv_ap_cm_s": "Anteroposterior mean velocity",
    "mv_ml_cm_s": "Mediolateral mean velocity",
    "ellipse_cm2": "95% prediction ellipse area",
    "mv_per_foot_length": "Resultant mean velocity divided by foot length",
}
