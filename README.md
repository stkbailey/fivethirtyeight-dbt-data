# FiveThirtyEight Data in DBT Format

This repository is a [`dbt`](https://www.getdbt.com) package containing data extracted from
[*FiveThirtyEight*'s data repository](https://github.com/fivethirtyeight/data).
The package is intended to be used as a way to rapidly load interesting, curated
data sets into your database of choice.

## Installing this package

To load data from this package, you'll need to install the package into your dbt project
just like any other package by adding it your `packages.yml` file and running `dbt deps`.

```{yaml}
packages:
    - git: "https://github.com/stkbailey/fivethirtyeight-open-data.git"
      revision: 0.1.0
```

Afterwards, you'll need to indicate which projects you'd like to load by specifying the folder
name in the `seeds` config block of `dbt_project.yml`. (Example below.) The next time you run 
`dbt seed`, the data will load!

```
seeds:
  fivethirtyeight:
    avangers:
      enabled: true
    tarantino:
      enabled: true
    fandango:
      enabled: true
```

## About this Package

Data in this package are pulled from FiveThirtyEight's data repository, then minimally processed
to makem them compliant with `dbt`. This includes, for each project:

1. Reformatting the `README.md` file into a `schema.yml` file.
2. Renaming all `csv` files to be `<project_name>_<file_name>.csv`.
3. Trimming large files (of a customizable size).

The code for re-downloading files is found in `download_and_process_files.py.`

## About the Data

See https://data.fivethirtyeight.com/ for a list of the data and code FiveThirtyEight has published.

Unless otherwise noted, these data sets are available under the
[Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/),
and the code is available under the [MIT License](https://opensource.org/licenses/MIT).
If you find this information useful, please [let us know](mailto:data@fivethirtyeight.com).
