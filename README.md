# Meta Data for Good - Bulk Downloader

Meta (formerly Facebook) offers academic partners many useful datasets about
crises around the world. In particular, Meta has been offering important datasets
about the COVID-19 crisis. The following datasets were of interest to our
research purposes:

- Facebook Population (Administrative Regions) v1
- Facebook Population (Tile Level) v1
- Movement Between Administrative Regions v1
- Movement Between Tiles v1
- Colocation

These data refer mainly to Facebook users, but they may as well be of use as a
good proxy to make estimates about the population of places (*Facebook Population*),
the movement of people between places (*Movement*) and the co-presence of people
coming from different places (*Colocation*).

This repository contains a little toolkit (`bulk_downloader`) to interact with
the website from a Python script. For our use case, the objects and methods
defined in the toolkit are being used in a script that guides the user through
the bulk download of datasets (`main.py`).

The script has been verified to work on 2022-10-09.

## Installation

The main dependencies of this package are `selenium`, `pandas` and `python-dotenv`.

In order to get the proper packages ready for use issue the following command.

```
poetry install
```

## Execution

The script can be executed by issuing the following command.

```
python main.py
```

The user will be guided through the choice of the datasets, mainly the choice
being limited to COVID-19 datasets from Italy for our research purposes. The
script can be accomodated to pursue any type of bulk download from the website.

Be warned that **the datasets** specified in the script (i.e. *Italy Coronavirus
Disease Prevention Map Feb 24 2020 Id*) **are discontinued and are soon going to be
dismissed from the platform**.

# Impressum

Shoichi Yip // 2022

This tool contributes to the **AIACE project** (UniTrento).

- Principal Investigator: [prof. Luca Tubiana](https://sbp.physics.unitn.it/luca-tubiana/)
- Postdoctoral Student: [dr. Jules Morand](https://sbp.physics.unitn.it/jules-morand/)
- Research Assistant: Shoichi Yip