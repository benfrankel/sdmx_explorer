# SDMX Explorer

**SDMX Explorer** is a Python CLI tool for downloading statistical data, allowing you to:

- Explore available SDMX datasets
- Construct queries into these datasets interactively
- TODO: Download data according to your saved queries (into a `.xlsx` file)

## Background

**SDMX** (**Statistical Data and Metadata eXchange**) is a set of standards for sharing statistical data.

The SDMX information model (**SDMX-IM**) includes the following terminology:

| Term          | Description                                          | Example      |
|---------------|------------------------------------------------------|--------------|
| **Source**    | A data source (organization, URL)                    | `IMF`        |
| **Dataflow**  | A dataset that may receive updates over time         | `CPI`        |
| **Dimension** | An axis of a dataset                                 | `COUNTRY`    |
| **Code**      | A valid value for a particular dimension             | `USA`        |

In order to request data, you must construct an SDMX data query.
This requires a source, dataflow, and **key** (to filter the data by dimension).

For example, for a dataflow with dimensions `FREQUENCY`, `SEX`, and `COUNTRY` in that order, the key `A.M.USA` filters for _annual_ data on _men_ from the _USA_.

You can match multiple codes for the same dimension with `+` (e.g. `USA+ISR`), or _all_ codes with `*`.
The key `*.*.*` matches the entire dataflow.

Note that in order to construct a valid key for a dataflow, you must at least know how many dimensions it has.

## Setup

Install Python 3.13.7 (or a compatible version), Pip, and SQLite.
Then, in this directory, run the following commands:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This sets up a virtual environment and installs the required Python dependencies in that environment.

## Usage

In this directory, enter the virtual environment if necessary:

```sh
source .venv/bin/activate
```

Now you can run the SDMX explorer:

```sh
./explore.py
```

Use the REPL to explore available SDMX datasets and construct queries into them.
