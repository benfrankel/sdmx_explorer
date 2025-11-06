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

Install Python 3.13 (or a compatible version), Pip, and SQLite.
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

Now you can launch the SDMX explorer REPL:

```sh
./explore.py
```

This will greet you with the following prompt:

```
SDMX Explorer
Commands: help, quit, list (select a source by entering its index or ID)
> 
```

Enter `help` to see the full list of commands.

### Example

Start by entering `list` to see a list of SDMX sources:

```
┏━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  # ┃ Source ID    ┃ Source Name                                                                                      ┃ Source URL                                                             ┃
┡━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│  0 │ ABS          │ Australian Bureau of Statistics                                                                  │ https://api.data.abs.gov.au                                            │
├────┼──────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│  1 │ ABS_JSON     │ Australian Bureau of Statistics                                                                  │ https://api.data.abs.gov.au                                            │
├────┼──────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│  2 │ AR1          │ Argentina                                                                                        │ https://sdds.indec.gob.ar/files/                                       │
├────┼──────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
...
├────┼──────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ 31 │ UY110        │ Uruguay                                                                                          │ https://sdmx-mtss.simel.mtss.gub.uy/rest                               │
├────┼──────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ 32 │ WB           │ World Bank World Integrated Trade Solution                                                       │ https://wits.worldbank.org/API/V1/SDMX/V21/rest                        │
├────┼──────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ 33 │ WB_WDI       │ World Bank World Development Indicators                                                          │ https://api.worldbank.org/v2/sdmx/rest                                 │
└────┴──────────────┴──────────────────────────────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────┘
```

You can select the `IMF_DATA` source by entering its index (`14`) or its ID (`IMF_DATA`):

```
Commands: help, quit, list (select a source by entering its index or ID)
> 14
Selected source: IMF_DATA
```

Enter `back` to go back and select a different source.
With a source selected, enter `list` to see its dataflows:

```
Commands: help, quit, list (select a source by entering its index or ID)
IMF_DATA> list
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  # ┃ Dataflow ID           ┃ Dataflow Name                                                                                ┃ Dataflow Description                                                                         ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│  0 │ AFRREO                │ Sub-Saharan Africa Regional Economic Outlook (AFRREO)                                        │ Sub-Saharan Africa Regional Economic Outlook (REO) provides information on recent economic   │
│    │                       │                                                                                              │ developments and prospects for countries in sub-Saharan Africa. Data for the REO for         │
│    │                       │                                                                                              │ sub-Saharan Africa are prepared in conjunction with the semi-annual World Economic Outlook   │
│    │                       │                                                                                              │ (WEO) exercises, spring and fall.                                                            │
├────┼───────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┤
│  1 │ ANEA                  │ National Economic Accounts (NEA), Annual Data                                                │ This dataset presents national, official estimates of annual expenditure-based Gross         │
│    │                       │                                                                                              │ Domestic Product (GDP), by economy.   Estimates are presented in nominal terms (current      │
│    │                       │                                                                                              │ prices) and volume terms (with the effect of price changes removed).                         │
├────┼───────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┤
...
├────┼───────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────────────────────┤
│ 70 │ WPCPER                │ Crypto-based Parallel Exchange Rates (Working Paper dataset WP-CPER)                         │ This dataset provides a cross-country indicator of parallel exchange rates based on crypto   │
│    │                       │                                                                                              │ markets. Parallel exchange rates are measured as the price of bitcoin on the local market    │
│    │                       │                                                                                              │ relative to the U.S. market. Suggested citation: Graf von Luckner, C., Koepke, R., &         │
│    │                       │                                                                                              │ Sgherri, S. (2024). “Crypto as a Marketplace for Capital Flight.” IMF Working Paper No.      │
│    │                       │                                                                                              │ 2024/133. International Monetary Fund. Data Management: Shuhan Yue                           │
└────┴───────────────────────┴──────────────────────────────────────────────────────────────────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────────────────────┘
```

You can select the `CPI` dataflow by entering its index (`6`) or its ID (`CPI`):

```
Commands: help, quit, list, info, back (select a dataflow by entering its index or ID)
IMF_DATA> 6
Selected dataflow: CPI
```

Enter `back` to go back and select a different dataflow.
With a dataflow selected, enter `list` to see its dimensions:

```
Commands: help, quit, list, info, back, data (select a dimension by entering its index or ID)
IMF_DATA/CPI(*.*.*.*.*)> list
┏━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # ┃ Dimension ID           ┃ Concept Name           ┃ Concept Description                                                                                                                                                ┃
┡━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 0 │ COUNTRY                │ Country                │ The country or region for which the data or statistics in a resource are collected or reported.                                                                    │
├───┼────────────────────────┼────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1 │ INDEX_TYPE             │ Index type             │ Type of index prices.                                                                                                                                              │
├───┼────────────────────────┼────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 2 │ COICOP_1999            │ Expenditure Category   │ The Classification of Individual Consumption According to Purpose (COICOP) 1999 is a standardized classification system developed by the United Nations Statistics │
│   │                        │                        │ Division to categorize household consumption expenditures by purpose. It includes 14 divisions, 47 groups, and 117 classes.                                        │
├───┼────────────────────────┼────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 3 │ TYPE_OF_TRANSFORMATION │ Type of Transformation │ Represents the specific calculations or computations applied to source data, along with the standard unit used to express the resulting new data elements or       │
│   │                        │                        │ indicators.                                                                                                                                                        │
├───┼────────────────────────┼────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 4 │ FREQUENCY              │ Frequency              │                                                                                                                                                                    │
└───┴────────────────────────┴────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

You can select the `COUNTRY` dimension by entering its index (`0`) or its ID (`COUNTRY`):

```
Commands: help, quit, list, info, back, data (select a dimension by entering its index or ID)
IMF_DATA/CPI(*.*.*.*.*)> 0
Selected dimension: COUNTRY
```

Enter `back` to go back and select a different dimension.
With a dimension selected, enter `list` to see its valid codes:

```
Commands: help, quit, list, info, back, data (select a code by entering its index or ID)
IMF_DATA/CPI(*.*.*.*.*)/COUNTRY> list
┏━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃   # ┃ Code ID ┃ Code Name                                                                  ┃ Code Description                                                                                                            ┃
┡━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│   0 │ ABW     │ Aruba, Kingdom of the Netherlands                                          │                                                                                                                             │
├─────┼─────────┼────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│   1 │ AFG     │ Afghanistan, Islamic Republic of                                           │                                                                                                                             │
├─────┼─────────┼────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│   2 │ AGO     │ Angola                                                                     │                                                                                                                             │
├─────┼─────────┼────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
...
├─────┼─────────┼────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 334 │ ZAF     │ South Africa                                                               │                                                                                                                             │
├─────┼─────────┼────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 335 │ ZMB     │ Zambia                                                                     │                                                                                                                             │
├─────┼─────────┼────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 336 │ ZWE     │ Zimbabwe                                                                   │                                                                                                                             │
└─────┴─────────┴────────────────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

You can select the `USA` code by entering its index (`317`) or its ID (`USA`):

```
Commands: help, quit, list, info, back, data (select a code by entering its index or ID)
IMF_DATA/CPI(*.*.*.*.*)/COUNTRY> USA
Added USA to COUNTRY
```

This adds `USA` to the `COUNTRY` dimension of the key.
You can always see the current key in the prompt (now the key is `USA.*.*.*.*`):

```
Commands: help, quit, list, info, back, data (select a code by entering its index or ID)
IMF_DATA/CPI(USA.*.*.*.*)/COUNTRY> 
```

You can select another `COUNTRY` code to add it to the key, or select the same code again to remove it from the key.
You can also enter `*` to clear all codes from the currently selected dimension (to match all countries).

Once you're satisfied with the key, enter `data` to download data using the query you've constructed:

```
Commands: help, quit, list, info, back, data (select a code by entering its index or ID)
IMF_DATA/CPI(USA.*.*.*.*)/COUNTRY> data
```

Finally, enter `exit` to exit the REPL when you're done:

```
Commands: help, quit, list, info, back, data (select a code by entering its index or ID)
IMF_DATA/CPI(USA.*.*.*.*)/COUNTRY> exit
```
