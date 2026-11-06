# Data license and attribution

These derived outputs do not redistribute the Human Balance Evaluation Database.

## License for this project's own materials

The original writing, code, tests, and figure design are under CC BY 4.0. See `LICENSE` and https://creativecommons.org/licenses/by/4.0/.

CC BY 4.0 does not apply to the Human Balance Evaluation Database and does not relicense it. The database is not in this project.

## What PhysioNet serves

The files used here are version 1.0.0 of the Human Balance Evaluation Database.

- Record: https://physionet.org/content/hbedb/1.0.0/
- Files: https://physionet.org/files/hbedb/1.0.0/
- Open bucket documented on that page: `s3://physionet-open/hbedb/1.0.0/`
- DOI: https://doi.org/10.13026/C2WW2W
- License page checked for this project: https://www.physionet.org/content/hbedb/view-license/1.0.0/

That license page is the Open Data Commons Attribution License v1.0 (ODC-BY 1.0):

https://opendatacommons.org/licenses/by/1.0/

ODC-BY allows use, including creation of analyses, with attribution. If a produced work from the database is shared publicly, the license asks for a notice that the content came from the database and is available under ODC-BY. A suitable notice is:

Contains information from the Human Balance Evaluation Database, version 1.0.0 (https://physionet.org/content/hbedb/1.0.0/), which is made available under the ODC Attribution License (https://opendatacommons.org/licenses/by/1.0/).

The database is provided without warranty. This project does not add a warranty.

## Disagreement with the 2016 article

Santos and Duarte (2016), in PeerJ, say that the PhysioNet copy was made available under the ODC Public Domain Dedication and License v1.0:

https://opendatacommons.org/licenses/pddl/1.0/

The license page served with PhysioNet version 1.0.0 at the time of this analysis is ODC-BY 1.0, not PDDL. Those statements do not match. This project follows the license text attached to the files that were downloaded. It does not treat the database as public domain.

The Figshare copy described in the same article is a separate distribution under CC-BY. This project downloads the PhysioNet WFDB files only.

## Attribution to use with any result from this project

Santos DA, Duarte M. A public data set of human balance evaluations. PeerJ. 2016;4:e2648. https://doi.org/10.7717/peerj.2648

Santos DA, Duarte M. A public data set of human balance evaluations. PeerJ Preprints. Posted 24 June 2016. https://doi.org/10.7287/peerj.preprints.2162v1

Santos DA, Duarte M. Human Balance Evaluation Database (version 1.0.0). PhysioNet. 2016. https://doi.org/10.13026/C2WW2W

Pollard T, Moody BE, Lehman LH, Gow BJ, Fernandes C, Xie C, Johnson A, Mark RG, Heldt T. PhysioNet as a global platform for biomedical research. Nature Health. 2026;1(8):792-795. https://doi.org/10.1038/s44360-026-00096-z

Goldberger AL, Amaral LAN, Glass L, Hausdorff JM, Ivanov PC, Mark RG, Mietus JE, Moody GB, Peng C-K, Stanley HE. PhysioBank, PhysioToolkit, and PhysioNet: components of a new research resource for complex physiologic signals. Circulation. 2000;101(23):e215-e220. https://doi.org/10.1161/01.CIR.101.23.e215

The DOI record for the preprint uses the title "A public data set of human balance evaluations." The PhysioNet landing page has also printed a short label, "A Public Database of Human Balance Evaluations," for that preprint. Cite the DOI title together with the dataset DOI. The PhysioNet record also asks for the Pollard and colleagues platform citation above. Initials and the issue number follow the DOI record (Lehman LH, Gow BJ, volume 1, issue 8, pages 792-795).

Methods citations used for the sway summaries:

Prieto TE, Myklebust JB, Hoffmann RG, Lovett EG, Myklebust BM. Measures of postural steadiness: differences between healthy young and elderly adults. IEEE Transactions on Biomedical Engineering. 1996;43(9):956-966. https://doi.org/10.1109/10.532130

Duarte M, Freitas SMSF. Revision of posturography based on force plate for balance evaluation. Brazilian Journal of Physical Therapy. 2010;14(3):183-192. https://doi.org/10.1590/S1413-35552010000300003

Duarte M. Comments on "Ellipse area calculations and their applicability in posturography" (Schubert and Kirchner, vol. 39, pages 518-522, 2014). Gait & Posture. 2015;41(1):44-45. https://doi.org/10.1016/j.gaitpost.2014.08.008

## What is not in git

`scripts/download_hbedb.py` downloads the WFDB recordings, `BDSinfo.txt`, and `RECORDS` into `data/raw/`. That directory is gitignored. `BDSinfo.txt` contains illness, medication, disability descriptions, and other interview fields. Derived tables in `outputs/` keep the design variables needed for the sway analysis and a yes or no disability flag. They do not keep those narratives.

Do not copy `data/raw/` into a public repository, a Kaggle dataset, or a hosted demo without deciding the license question above and removing fields that are not needed.
