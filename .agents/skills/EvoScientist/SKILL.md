```markdown
# EvoScientist Development Patterns

> Auto-generated skill from repository analysis

## Overview

This skill documents the core development patterns, coding conventions, and collaborative workflows used in the EvoScientist repository. The codebase is primarily Python, with a focus on research artifact management, reproducible experiments, and rigorous documentation. No external framework is detected, and the repository emphasizes clarity, maintainability, and provenance in scientific workflows.

## Coding Conventions

### File Naming

- Use **snake_case** for all Python files and modules.
  - Example: `data_loader.py`, `experiment_utils.py`

### Import Style

- Prefer **relative imports** within the package.
  - Example:
    ```python
    from .utils import normalize_data
    ```

### Export Style

- Use **named exports** for clarity.
  - Example:
    ```python
    def run_experiment(...):
        ...
    __all__ = ['run_experiment']
    ```

### Commit Messages

- Follow **conventional commit** patterns.
- Supported prefixes: `style:`, `docs:`, `feat:`
- Example:
  ```
  feat: add validation script for new experiment stage
  style: normalize punctuation in SKILL.md
  docs: update references for J-space artifact
  ```

## Workflows

### Add or Update J-space Research Artifact

**Trigger:** When introducing or updating a J-space research operation, experiment stage, or its documentation and validation.

**Command:** `/new-jspace-artifact`

1. Create or update `SKILL.md` in `EvoScientist/skills/jspace-research-operations/`.
2. Add or update reference documentation in `EvoScientist/skills/jspace-research-operations/references/`.
3. Add or update validation scripts in `EvoScientist/skills/jspace-research-operations/scripts/`.
   - Example script:
     ```python
     # scripts/validate_experiment.py
     def validate():
         # validation logic here
         pass
     ```
4. Add or update evidence report templates in `EvoScientist/skills/jspace-research-operations/templates/`.
5. Add or update Colab notebooks and provenance records in `sakshi notes/`.
6. Update `docs/README.md` and related architecture docs if relevant.
7. Use a relevant commit message, e.g., `feat: add new experiment validation script`.

### Style Standardization on J-space Artifacts

**Trigger:** When enforcing consistent style or formatting in J-space documentation and notebooks.

**Command:** `/style-fix`

1. Identify style inconsistencies (e.g., punctuation, em dashes, colons) in `SKILL.md`, provenance, or experiment docs.
2. Edit affected files to standardize style.
3. Commit changes with a `style:` prefix.
   - Example commit message:
     ```
     style: standardize punctuation in references and provenance records
     ```

## Testing Patterns

- Test files follow the pattern: `*.test.*`
  - Example: `data_loader.test.py`
- Testing framework is not explicitly specified; standard Python testing patterns are recommended.
- Place test files alongside the modules they test or in a dedicated `tests/` directory.

  Example test file:
  ```python
  # data_loader.test.py
  from .data_loader import load_data

  def test_load_data():
      assert load_data("sample.csv") is not None
  ```

## Commands

| Command              | Purpose                                                        |
|----------------------|----------------------------------------------------------------|
| /new-jspace-artifact | Add or update a J-space research skill, experiment, or docs    |
| /style-fix           | Standardize style and formatting across J-space documentation  |
```
