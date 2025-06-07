# Code Generator Window

This dialog configures how log lines are converted to CEF and generates the Python converter. It opens from the main window via the **Code Generator** menu item.

## CEF Header Section

At the top is a **CEF Header** frame with fields for the standard header values. The defaults are:

- `CEF Version` (read only) – always `0`.
- `Device Vendor` – `ACME`.
- `Device Product` – `LogParserPro`.
- `Device Version` – `1.0.0`.
- `Event Class ID` – `42`.
- `Event Name` – `LoginAttempt`.
- `Severity (int)` – `5`.

The version field cannot be edited.

## Mapping List

The **Fields Auto-Mapped from Regex Patterns** area displays mapping rules that associate regex patterns with CEF fields. Each row contains:

1. **CEF Field** – the target CEF key.
2. **Pattern** – drop-down with a regex name or an input for constants.
3. **Regex** – the corresponding pattern text (read only).
4. **Transform** – button to select value transformation.
5. **Example** – matching text from the loaded log or the constant value.
6. **Result** – example after applying the transform.
7. A delete button for optional fields.

Click **+ Add Field** to add another mapping using any supported CEF key.

Rows for the mandatory fields `deviceVendor`, `deviceProduct`, `deviceVersion`, `signatureID`, `name` and `severity` are created automatically. The first three may use constants. When `signatureID` has no pattern or value, an `incremental` rule (event counter) is used.

## Control Buttons

Below the list are buttons to manage the configuration:

- **Save Config** – store the current mapping using the log file key.
- **Preview Code ▸** – generate files in a temporary directory and display `cef_converter.py` in a new window.
- **Generate Python** – generate `cef_converter.py` and `main_cef_converter.py` in a `generated_cef` folder next to the application.

Settings are saved automatically when the window is closed.

## Selecting and Transforming Values

Each mapping can specify how a value is transformed. Clicking **Transform** opens the `TransformEditorDialog`. Built-in formats include `lower`, `upper`, `capitalize`, `sentence` and `time`. Advanced options cover value maps, token replacement and reordering. For fields in the `Time` category a warning about ISO‑8601 conversion is shown automatically.

## Finding Examples

Examples are computed on the fly. If a mapping uses a regex, the first matching fragment from the loaded log lines is shown. For constants, the entered value is used. After selecting a transform the example is processed with `apply_transform` and displayed in **Result**.

## Saving the Configuration

Only the CEF version and the mapping list are persisted. Other header values are restored from constants when generating code. This behavior is implemented in the `_save_config` method of `CodeGeneratorDialog`.

