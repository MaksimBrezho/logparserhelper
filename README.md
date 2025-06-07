# Log Parser Helper

Log Parser Helper is a collection of utilities and a desktop GUI for
experimenting with log formats. It lets you build regular expressions,
highlight log files, and generate code that converts logs to the CEF
(Common Event Format).

## Features

- **Tkinter GUI** for viewing logs and enabling/disabling regex patterns.
- **Pattern Wizard** that creates draft regular expressions from selected
  log lines with advanced controls for numbers, case sensitivity and
  prefix merging.
- **Built‑in patterns** for common timestamps and messages plus support
  for per‑log and user‑defined patterns.
- **Coverage highlighting** shows which parts of the log are matched by
  active patterns and calculates the percentage of covered characters.
- **Code generator** that produces a Python converter for CEF. Mapping
  rules support value transformations, replacements, token reordering and
  incremental counters.
- **Sample log files** in `data/sample_logs` for quick experimentation.

## Installation

1. Ensure Python 3.11 or newer is available.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

If the environment lacks internet access, preinstall the packages from
`requirements.txt` into a virtual environment and reuse it.

## Running the application

Launch the GUI with:

```bash
python main.py
```

Open a log file with the **Load Log** button, select lines and run the
**Create Pattern** wizard to build new patterns. Use **Save Patterns**
to store per‑log patterns, or the **Code Generator** to produce a CEF
converter.

## Building an installer

To produce a standalone executable you need [PyInstaller](https://pyinstaller.org).
Install it and run the helper script:

```bash
pip install pyinstaller
python build_installer.py
```

The resulting installer binary `ALLtoCEF` will be placed in the `dist`
directory and will use the icon from `icon/ALLtoCEF.ico`. The helper script
also bundles this icon together with the required built-in pattern and CEF
data files.

## Running the tests

The repository includes an extensive test suite. Execute it with:

```bash
pytest -q
```

All tests should pass after the dependencies are installed.

## Transformations

When defining mapping rules for the code generator, several helper
transformations are supported:

- `lower`, `upper`, `capitalize`, `sentence`
- `time` – detects many common date/time formats via `python-dateutil`
  and converts them to `YYYY-MM-DDTHH:MM:SSZ`.

Transformations can also specify token reordering, value replacement and
value maps. See `utils/transform_logic.py` for full details.

## Project structure

```
core/   – regex builder, tokenizer and highlighting logic
utils/  – JSON helpers, color utilities and the code generator
gui/    – Tkinter user interface modules
data/   – built‑in patterns, CEF field definitions and sample logs
```

Mappings created automatically for CEF fields of the `Time` category
use this transformation by default.

## Documentation

Detailed explanations of each window and tool are available in the
[docs](docs/) directory.

## UML Diagrams

Automatically generated class and package diagrams are in [docs/uml](docs/uml).
