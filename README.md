# `target-hubspot`

Custom target for HubSpot built with the Meltano SDK.

Built with the [Meltano Singer SDK](https://sdk.meltano.com).

## Settings

| Setting       | Required | Default | Description                                                                                                             |
|:--------------|:--------:|:-------:|:------------------------------------------------------------------------------------------------------------------------|
| client_id     | True     | None    | The Client ID of your OAuth application.                                                                                |
| client_secret | True     | None    | The Client Secret of your OAuth application.                                                                            |
| refresh_token | True     | None    | The refresh token of the user whose data you're syncing.                                                                |
| object_type   | True     | None    | The object type you'd like to make updates to. As of 11/30/23, only `contacts`, `companies`, and `deals` are supported. |

## Getting Started

```shell
pyenv install # installs Python version in `.python-version`
python -m pip install poetry # install poetry if you don't have it yet
python -m venv venv # create venv for isolated dependencies
source venv/bin/activate # activate venv
poetry install # install deps
```

Brief overview of the important files and functions:

```shell
target_hubspot/
  remote/ # anything that touches the HubSpot API
    authentication.py # handles refreshing OAuth tokens; HubSpot provides very short-lived tokens of only 30s
    client.py # wrapper around HubSpot API
    model.py # API-specific models
  constants.py # a few hardcoded strings that didn't fit elsewhere
  context.py # base class a few others inherit from to get easy access to the config and logger
  decorators.py # bit of retry logic in here
  encoder.py # need a few serialization shims to convert from Singer stuff to JSON-serializable
  exceptions.py # one or two custom exceptions, nothing special
  model.py # domain models used throughout the service (distinct from remote/models.py, where API-specific models are
  pydantic_config.py # base config all other pydantic models inherit from
  sinks.py # MAIN ENTRYPOINT. A `process_batch()` function here is the entrypoint of note.
  target.py # ALSO IMPORTANT. Defines parameters we expect to be provided.
```

The only truly notable one is `sinks.py`. This is the main entrypoint.

## Batching

Meltano provides two main sink interfaces that would be applicable here - `RecordSink` and `BatchSink`.

- `RecordSink` uses `process_record()` as its main entrypoint and goes one at a time
- `BatchSink` uses `process_batch()` as its main entrypoint and provides you hundreds of records at once

We consciously use `BatchSink` and use HubSpot's batch update endpoints where possible because it's a _lot_ more efficient regarding rate limits. HubSpot limits OAuth tokens to 1,000 calls per ten minutes, which honestly isn't a ton if we're syncing massive amounts of data.

## Testing

Running tests is easy. First, add your config parameters to `.secrets/config.json` (is under `.gitignore` - you will have to create the file):

```json
{
  "client_id": "5a50...",
  "client_secret": "b3df...",
  "refresh_token": "2e3c...",
  "object_type": "contacts"
}
```

You can get these parameters by authenticating into HubSpot in staging, then finding your credentials in the credentials collection in Firestore.

If you don't have access to the HubSpot Sandbox Account, talk to Matt Hanselman, Matt Hall or Anden Acitelli and we'll get you access.

Then, run them:

```shell
poetry run pytest .
```

The main test entrypoint, at time of writing, is `tests/test_core.py`. Tests pull JSONL files adhering to the Singer spec from `tests/resources/*.json.`, and feed them line-by-line to the target, asserting that no exceptions are thrown.