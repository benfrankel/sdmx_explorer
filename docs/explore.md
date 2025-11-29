# Explorer

The explorer is an interactive [REPL](https://en.wikipedia.org/wiki/Read%E2%80%93eval%E2%80%93print_loop)
that allows you to explore the structure of SDMX dataflows and construct data queries.

## Usage

Run `explore` to launch the REPL. You will be greeted by the initial prompt:

```
SDMX Explorer
Commands: help, quit, list
> 
```

The basic workflow looks something like this:

1. Enter `list` to see a list of SDMX sources, dataflows, dimensions, or codes.
2. Enter an index or ID from the list to select it.
3. If you want to select something else, enter `back`.
4. If you're done, enter `quit`. Otherwise return to step 1.

Enter `help` for the full list of commands.

## Tips

- **Shortcuts:**
    - Every command has a one-letter shortcut for convenience. You can type `l` instead of `list`, or `b` instead of `back`, and so on.
    - Use Ctrl-C to cancel a command that's taking too long or reset your input text.
    - Use Ctrl-D with no input text to go `back`.
- **Advanced selection:**
    - Enter a sequence of selections separated by `/` to select all of them (e.g. `IMF_DATA/ANEA`).
    - Enter a path with a leading `/` to switch to it from anywhere (e.g. `/IMF_DATA/ANEA/*.B11.Q.XDC.A`).
    - With a dataflow selected, enter an entire key to select it (e.g. `*.B11.Q.XDC.A`).
    - With a dimension selected, enter `*` to reset all of its codes.
    - With a dimension selected, enter multiple codes separated by `+` to select all of them.
    - You can still use both indices and IDs during any advanced selection.
- **Bookmarks:**
    - Enter `:` to add or remove the current path as a bookmark.
    - Enter `:list` to list bookmarks.
    - Enter `:<INDEX>` to select a bookmark.

## Walkthrough

Start by entering `list` to see a list of SDMX sources:

```
┏━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  # ┃ Source ID    ┃ Source Name                                                                                      ┃ Source URL                                                             ┃
┡━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│  0 │ ABS          │ Australian Bureau of Statistics                                                                  │ https://api.data.abs.gov.au                                            │
├────┼──────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│  1 │ ABS_JSON     │ Australian Bureau of Statistics                                                                  │ https://api.data.abs.gov.au                                            │
├────┼──────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
...
├────┼──────────────┼──────────────────────────────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ 33 │ WB_WDI       │ World Bank World Development Indicators                                                          │ https://api.worldbank.org/v2/sdmx/rest                                 │
└────┴──────────────┴──────────────────────────────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────┘
```

You can select the `IMF_DATA` source by entering its index (`14`) or its ID (`IMF_DATA`):

```
Commands: help, quit, list
> 14
Selected source: IMF_DATA
```

Enter `back` to go back and select a different source.

With a source selected, enter `list` to see its dataflows:

```
Commands: help, quit, list
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
Commands: help, quit, list, info, back
IMF_DATA> 6
Selected dataflow: CPI
```

Enter `back` to go back and select a different dataflow.

With a dataflow selected, enter `list` to see its dimensions:

```
Commands: help, quit, list, info, back, save
IMF_DATA/CPI/*.*.*.*.*> list
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
Commands: help, quit, list, info, back, save
IMF_DATA/CPI/*.*.*.*.*> 0
Selected dimension: COUNTRY
```

Enter `back` to go back and select a different dimension.

With a dimension selected, enter `list` to see its valid codes:

```
Commands: help, quit, list, info, back, save
IMF_DATA/CPI/COUNTRY=*.*.*.*.*> list
┏━━━━━┳━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃   # ┃ Code ID ┃ Code Name                                                                  ┃ Code Description                                                                                                            ┃
┡━━━━━╇━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│   0 │ ABW     │ Aruba, Kingdom of the Netherlands                                          │                                                                                                                             │
├─────┼─────────┼────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│   1 │ AFG     │ Afghanistan, Islamic Republic of                                           │                                                                                                                             │
├─────┼─────────┼────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
...
├─────┼─────────┼────────────────────────────────────────────────────────────────────────────┼─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 336 │ ZWE     │ Zimbabwe                                                                   │                                                                                                                             │
└─────┴─────────┴────────────────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

You can select the `USA` code by entering its index (`317`) or its ID (`USA`):

```
Commands: help, quit, list, info, back, save
IMF_DATA/CPI/COUNTRY=*.*.*.*.*> USA
Added USA to COUNTRY
```

This adds `USA` to the `COUNTRY` dimension of the key.
You can always see the current key in the prompt. For example, right now the key is `USA.*.*.*.*`:

```
Commands: help, quit, list, info, back, save
IMF_DATA/CPI/COUNTRY=USA.*.*.*.*> 
```

You can select another `COUNTRY` code to add it to the key, or select the same code again to remove it from the key.
You can also enter `*` to clear any selected codes and return to matching anything.

Once you're satisfied with the key, enter `save` to bookmark the query you've constructed to `bookmarks.txt`:

```
Commands: help, quit, list, info, back, save
IMF_DATA/CPI/COUNTRY=USA.*.*.*.*> data
```

Finally, you can enter `exit` to leave the REPL:

```
Commands: help, quit, list, info, back, save
IMF_DATA/CPI/COUNTRY=USA.*.*.*.*> exit
```

