# SDMX Explorer

**SDMX Explorer** is a Python CLI tool for downloading statistical data via [SDMX](https://sdmx.org/about-sdmx/welcome/), allowing you to:

- Explore available data
- Construct data queries interactively
- Download data from a list of data queries

## Background

**SDMX** (**Statistical Data and Metadata eXchange**) is a set of standards for sharing statistical data.

The SDMX information model (**SDMX-IM**) includes the following terminology:

| Term          | Description                                          | Example      |
|---------------|------------------------------------------------------|--------------|
| **Source**    | A data source (organization, URL)                    | `IMF`        |
| **Dataflow**  | A dataset that may receive updates over time         | `CPI`        |
| **Dimension** | An axis of a dataset                                 | `COUNTRY`    |
| **Code**      | A valid value for a particular dimension             | `USA`        |

In order to request data, you must construct an SDMX data query out of a source, dataflow, and **key** (which filters the data by dimension).

For example, in a dataflow with dimensions `[FREQUENCY, SEX, COUNTRY]`, the key `A.M.USA` could filter for _annual_ data on _men_ from the _USA_.

You can accept multiple codes for the same dimension with `+` (e.g. `USA+ISR`), or _any_ code with `*`.
For example, the key `*.*.*` would match the entire dataflow.

Note that in order to construct a valid key for a dataflow, you must at least know how many dimensions it has.

## Setup

Install Python 3.13+, Pip, and SQLite.
Then, in this directory, run the following commands:

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

This one-time setup creates a virtual environment and installs the SDMX Explorer there.

## Usage

Run `source .venv/bin/activate` to enter the virtual environment.

The virtual environment makes the following commands available:

- [`explore`](./docs/explore.md)
- [`download`](./docs/download.md)

Follow the links for more information.

## License

The source code in this repository is made available under the [MIT License](./LICENSE-MIT.txt).
