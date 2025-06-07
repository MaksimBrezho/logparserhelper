# 🧙 Pattern Wizard

This document describes all aspects of the Pattern Wizard dialog located in `gui/pattern_wizard.py`. The wizard assists in creating regular expression patterns from sample log lines.

## Purpose

Pattern Wizard provides an interactive workflow to build draft regular expressions from selected log fragments. Users can tweak generation parameters, preview matches across the log and save new patterns that will be used by the main application.

## Launching

In the main window select text in the log viewer and click **Create Pattern**. The application gathers the selected fragments, asks for a name for per‑log patterns and then opens the wizard.

## Interface Overview

1. **Menu** – contains a single **Save** item with shortcut `Ctrl+S`.
2. **Name** and **Category** – fields displayed at the top. The category value is selected automatically based on chosen CEF fields (see below).
3. **Toggle advanced options** – shows or hides additional parameters.
4. **Advanced parameters**:
   - **Ignore case** – compile the regex with the `re.IGNORECASE` flag.
   - **Number mode** – controls how numeric tokens are generalised. Options include: Standard, Fixed length, Always `\d+`, Set minimum length, and Fixed or minimum length.
   - **Min number length** – used by some number modes.
   - **Merge text** – treat different words as a single token column.
   - **Use |** – prefer enumerations (`foo|bar`) when appropriate.
   - **Prefix merge** – merge alternatives sharing common prefix and suffix.
   - **Max options** – maximum length of enumerations created by the regex builder.
   - **Window left/right** – optional look‑behind and look‑ahead anchors for the fragment window.
5. **Generated regular expression** – editable text area showing the draft regex. Below it is the snippet combobox used to insert common regex fragments.
6. **Undo** – the “← Previous” button restores the previous regex from history (`Ctrl+Z`).
7. **Update** – regenerates the regex from the current examples and parameters (`Ctrl+R`).
8. **Apply** – compiles the regex and shows matches in the preview area (`Ctrl+Enter`).
9. **Examples** – list of selected fragments. Buttons allow deleting entries (`Delete`) or adding a new selection from the preview (`Ctrl+A`).
10. **Matches preview** – shows lines from the log with matches highlighted. The view can display matching lines, absent lines or lines with multiple matches (conflicts). Use `Alt+Left`/`Alt+Right` to navigate pages.
11. **CEF Fields** – searchable list of CEF field checkboxes. The selected set determines the category, which updates automatically. Tooltip hints show field descriptions and examples.

## Snippets

The snippet dropdown provides quick insertion of common regex parts such as:

- One word (`\S+`)
- Letters only word (`[a-zA-Z]+`)
- Digits only (`\d+`)
- Alphanumeric word (`[a-zA-Z0-9]+`)
- Word of any characters (`[^ \t\n\r\f\v]+`)
- Line to end (`.*`)
- Line to end (non‑greedy) (`.*?`)
- Fixed length number (3) (`\d{3}`)
- Number with at least N digits (`\d{2,}`)
- Chars until colon (`[^:]+`)
- Segment in `[]` (`\[[^\]]+\]`)
- Segment in `()` (`\([^)]+\)`)
- Line with tag (`[a-zA-Z0-9._-]+:`)

Selecting a snippet inserts the corresponding regex text into the regex editor.

## Regex Generation

The wizard uses `core.regex.regex_builder.build_draft_regex_from_examples` to produce a regex from the examples. The function accepts the advanced parameters described above and analyses token columns across the example lines. It recognises key–value pairs and can merge tokens or build enumerations. The generated regex is stored in the history so the **← Previous** button can revert changes.

Applying the regex highlights matches in the preview widget using `core.regex_highlighter.apply_highlighting` with a yellow highlight color.

## Saving Patterns

The **Save** action collects the name, category, regex text and selected CEF fields. The data is written to `user_patterns.json` and to per‑log patterns via helpers from `utils.json_utils` (`save_user_pattern` and `save_per_log_pattern`). After saving the dialog closes.

## Auto category selection

As CEF fields are checked or unchecked the wizard chooses the category automatically. If all selected fields belong to the same category, that category is set. When fields from multiple categories are selected the special value “Multiple” is used.

## Tests

`tests/test_pattern_wizard.py` exercises core helper methods:

- `_on_digit_mode_change` – ensures the internal value matches the displayed choice.
- `_push_history` and `_undo_regex` – verify regex history handling.
- `_toggle_advanced` – toggles the advanced options frame visibility.
- `_filter_cef_fields` – filters the list of fields by search query.
- `_auto_select_category` – updates the category label based on selected fields.
- `_on_snippet_selected` – inserts snippet text into the regex entry.

## UML Diagrams

Class and package diagrams generated with PlantUML are located in `docs/uml`. The `classes_LogParserHelper.plantuml` diagram lists all attributes of `PatternWizardDialog` and other GUI classes.

## Summary

Pattern Wizard is a comprehensive tool for crafting new log patterns. It guides users from selecting example lines through tuning generation settings, previewing results and finally saving the pattern for later use.
