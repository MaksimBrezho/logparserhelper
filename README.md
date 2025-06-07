# Log Parser Helper

This project provides helper utilities and a GUI for building log parsing
patterns and analyzing logs.

## Installation

Install dependencies with `pip` using the included requirements file:

```bash
pip install -r requirements.txt
```

Note that `pip` may need Internet access to download packages. If your
environment does not have Internet access, use a preconfigured virtual
environment containing the requirements.

## Running the tests

Execute the automated tests with `pytest`:

```bash
pytest -q
```

Make sure you have the required dependencies installed before running
the tests.

## Transformations

When configuring mappings, several value transformations are available:

- `lower`, `upper`, `capitalize`, `sentence`
- `time` &mdash; automatically detects common date/time formats using
  `python-dateutil` and converts them to `YYYY-MM-DDTHH:MM:SSZ`.

Mappings created automatically for CEF fields of the `Time` category
use this transformation by default.

## UML Diagrams

Automatically generated class and package diagrams are in [docs/uml](docs/uml).
