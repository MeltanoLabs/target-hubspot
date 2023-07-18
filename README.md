# `target-hubspot`

Sample target for HubSpot.

Built with the [Meltano Singer SDK](https://sdk.meltano.com).

## Capabilities

* `about`
* `stream-maps`
* `schema-flattening`

## Settings

| Setting             | Required | Default | Description |
|:--------------------|:--------:|:-------:|:------------|
| access_token        | True     | None    | Your HubSpot private app API access token. See the [docs](https://developers.hubspot.com/docs/api/private-apps) for more details. |
| column_mapping      | True     | None    | An array including an object entry for each column in your import file stream. |
| date_format         | False    | YEAR_MONTH_DAY | The format for dates included in the import file stream. |
| import_operations   | False    | UPDATE  | Used to indicate whether the import should create and update, only create, or only update records for a certain object or activity. |
| stream_maps         | False    | None    | Config object for stream maps capability. For more information check out [Stream Maps](https://sdk.meltano.com/en/latest/stream_maps.html). |
| stream_map_config   | False    | None    | User-defined config values to be used within map expressions. |
| flattening_enabled  | False    | None    | 'True' to enable schema flattening and automatically expand nested properties. |
| flattening_max_depth| False    | None    | The max depth to flatten schemas. |

A full list of supported settings and capabilities is available by running: `target-hubspot --about`

## Supported Python Versions

* 3.8
* 3.9
* 3.10
* 3.11

## Usage

You can easily run `target-hubspot` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Target Directly

```bash
target-hubspot --version
target-hubspot --help
# Test using the "Carbon Intensity" sample:
tap-carbon-intensity | target-hubspot --config /path/to/target-hubspot-config.json
```

## Developer Resources

Follow these instructions to contribute to this project.

### Initialize your Development Environment

```bash
pipx install poetry
poetry install
```

### Create and Run Tests

Create tests within the `tests` subfolder and
  then run:

```bash
poetry run pytest
```

You can also test the `target-hubspot` CLI interface directly using `poetry run`:

```bash
poetry run target-hubspot --help
```

### Testing with [Meltano](https://meltano.com/)

_**Note:** This target will work in any Singer environment and does not require Meltano.
Examples here are for convenience and to streamline end-to-end orchestration scenarios._

Next, install Meltano (if you haven't already) and any needed plugins:

```bash
# Install meltano
pipx install meltano
# Initialize meltano within this directory
cd target-hubspot
meltano install
```

Now you can test and orchestrate using Meltano:

```bash
# Test invocation:
meltano invoke target-hubspot --version
# OR run a test `elt` pipeline with the Carbon Intensity sample tap:
meltano run tap-carbon-intensity target-hubspot
```

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the Meltano Singer SDK to
develop your own Singer taps and targets.
