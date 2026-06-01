---
name: python-docstring-standard
description: Project standard for documenting Python. Apply whenever writing or editing Python modules, classes, or functions. Every new or modified module, class, and public function/method gets a docstring in the same edit, keeping docstring coverage above the 80% pre-merge threshold so the gap never appears.
---

# Python Docstring Standard

Document Python as you write it. The goal is prevention: no definition ever ships without a docstring, so docstring coverage never drops below the 80% pre-merge threshold in the first place.

## The rule

When you create or edit a module, class, or public function/method, write its docstring in the **same edit**. Never leave a new definition undocumented and never plan to "add docstrings later."

Document:
- Every module (first line of the file, including each package `__init__.py`)
- Every class
- Every public function and method

Skip:
- `tests/` (excluded from coverage)
- Dunder/magic methods (`__init__`, `__repr__`, ...)

## Style

Terse one-line PEP 257: imperative mood, fits on one line, ends with a period. Match the surrounding code.

Write the docstring at the moment you write the definition:

```python
async def run(self, user_prompt: str) -> DecisionRoomState:
    """Execute Phases 0-3 for the prompt and return the final state."""
    state = DecisionRoomState(...)
```

Module / package docstring example:

```python
"""Orchestration package: pipeline engine and shared run state."""
```

## Safety net (final check, not the workflow)

The point of this skill is to never need a fix-up pass. As a last check before finishing a Python change, optionally confirm coverage still passes:

```bash
python -s -m interrogate --fail-under 80 .
```

(`-s` avoids a pytest `py.py` shim in the user site-packages that otherwise breaks interrogate.) If interrogate is unavailable, use the bundled fallback:

```bash
python .cursor/skills/python-docstring-standard/scripts/audit_docstrings.py .
```

`RESULT: PASSED` means the standard held. The threshold lives in `pyproject.toml` under `[tool.interrogate]`.
