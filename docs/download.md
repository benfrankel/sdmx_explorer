# Downloader

The downloader is a [CLI](https://en.wikipedia.org/wiki/Command-line_interface)
tool that can download SDMX data from a list of data queries.

## Usage

Start by writing a **download configuration file** in [TOML](https://en.wikipedia.org/wiki/TOML) or [YAML](https://en.wikipedia.org/wiki/YAML).

You can use this `example.toml` as a starting point:

```toml
# A list of columns to remove.
# Default: []
drop_columns = []
# If true, SDMX attribute columns will be removed.
# Default: false
drop_attributes = false
# If true, each row will contain an entire time series instead of a single observation.
# Default: false
pivot_table = false
# If true, the result of each data query will be saved to disk.
# Default: true
use_cache = true
# The file path where the download should be saved.
# Supported file extensions: .tsv, .csv, .xlsx, .xls, .html, .json, .parquet, .feather, .pkl, .pickle, .tex, .dta.
output_path = "example.tsv"
# The list of SDMX data queries to run.
queries = [
    "IMF_DATA/ANEA/AGO.B11.Q.XDC.A",
    "IMF_DATA/CPI/USA.CPI._T.IX.A",
]
```

Now run `download example.toml` to begin the download
(replace `example.toml` with the path to your download configuration file).

You can pass multiple download configuration files to `download` to run all of them.
