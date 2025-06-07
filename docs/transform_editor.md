# Transform Editor Window

The Transform Editor is a dialog used when defining mapping rules for the CEF code generator. It lets you configure how extracted values should be formatted, replaced or reordered before being assigned to a specific CEF field.

## Layout Overview

The window is created by `TransformEditorDialog` in `gui/transform_editor.py`. It contains the following elements:

1. **Regex display** – shows the regular expression associated with the current mapping, if one was provided when the dialog was opened.
2. **Examples list** – displays sample values for the field. Each example is shown both before and after transformation.
3. **Formatting options** – a set of radio buttons for the basic string transforms:
   - `none` – keep the text as is
   - `lower` – convert to lower case
   - `upper` – convert to upper case
   - `capitalize` – capitalize every word
   - `sentence` – capitalize only the first word
4. **Value map** – a multi‑line text box where each line contains `key=value`. Matching input values are replaced by the corresponding output.
5. **Replace if pattern matches** – two entry fields where you can specify a regular expression and the replacement text. If the regex matches, the value is replaced.
6. **Advanced token options** – when a regex is available, a checkbox reveals controls for reordering or dropping tokens. Tokens are detected from the best matching example and can be dragged to rearrange or removed with <kbd>Delete</kbd>.
7. **Preview area** – shows the examples with the selected transformation applied so you can verify the result before saving.
8. **Save and Cancel buttons** – apply the current settings or close the dialog without saving.

## Resulting Specification

When you click **Save**, the dialog returns a transformation definition. For simple cases this is just one of the formatting strings above. If other fields were filled in, a dictionary is returned with keys:

- `format` – one of the basic formatting modes
- `value_map` – mapping of input values to replacements (optional)
- `replace_pattern` / `replace_with` – regex substitution (optional)
- `token_order` and `regex` – list describing how tokens were reordered (optional)

This spec is later used by `utils.transform_logic.apply_transform` to convert values during log processing.
