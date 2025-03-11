# Conventions

- Give attributes types in class's __init__ immediately.
- Use type hints for all function parameters and return values.
- Use type hints for all local variables.
- Use list over List, dict over Dict, str | None instead of Optional[str], str | int instead of Union[str, int], etc.
- Treat python as a meticulously statically typed language.
- Wrap each arg to a newline in a function if it has more than 2 args.
- Don't use title-case types from the typing module, this includes Optional and Union. Use `from __future__ import annotations` to allow type hints to be evaluated at runtime (e.g. `str | None`).
- Prefer fast-exit functions over nested conditionals, inverse conditionals to make this happen.
- Consider how the program will continue if an exception is raised unexpectedly, and ensure that it does so gracefully.
- (if using qt in python) always import from qtpy.QtWidgets, qtpy.QtGui, and qtpy.QtCore etc instead of PyQt/PySide.
- Use pylance/ruff rules.
- Prefer double quotes over single quotes.
- Always use absolute import paths
- Ensure we're looking at reference material before making any changes to files
- Always read the existing file before making changes to that file.
- Keep existing files intact if possible
- Always check the write folder to ensure we are not writing code that already exists in a different source file. This is crucial for integraiton.
- always use powershell commnds if you need to execute commands, and DO NOT use 'powershell -Command' obviously the raw powershell command.
