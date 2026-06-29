```markdown
# opia Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches the core development conventions and workflows used in the `opia` Python repository. You'll learn how to structure code, write commits, organize files, and run or write tests in accordance with the project's established patterns. This guide is ideal for contributors aiming for consistency and maintainability in their code contributions.

## Coding Conventions

### File Naming
- Use **snake_case** for all Python files.
  - Example: `my_module.py`, `data_processor.py`

### Import Style
- Use **relative imports** within the package.
  - Example:
    ```python
    from .utils import helper_function
    ```

### Export Style
- Use **named exports** (explicitly define what is exported).
  - Example:
    ```python
    __all__ = ['MyClass', 'my_function']
    ```

### Commit Messages
- Follow **conventional commit** style.
- Use the `feat` prefix for new features.
- Keep commit messages concise (average ~60 characters).
  - Example:
    ```
    feat: add user authentication middleware
    ```

## Workflows

### Feature Development
**Trigger:** When implementing a new feature  
**Command:** `/feature-dev`

1. Create a new branch for your feature.
2. Write code using snake_case file names and relative imports.
3. Use named exports in your modules.
4. Write a commit message starting with `feat:` and a concise description.
5. Push your branch and open a pull request.

### Code Review Preparation
**Trigger:** Before submitting code for review  
**Command:** `/prepare-review`

1. Ensure all files follow snake_case naming.
2. Check that all imports are relative within the package.
3. Make sure `__all__` is defined for named exports.
4. Review commit messages for conventional style.

## Testing Patterns

- Test files are expected to follow the `*.test.ts` pattern.
- The specific testing framework is **unknown**; check existing test files for examples.
- Place test files alongside or near the modules they test.
- Example test file name: `my_module.test.ts`

## Commands
| Command         | Purpose                                        |
|-----------------|------------------------------------------------|
| /feature-dev    | Start a new feature development workflow        |
| /prepare-review | Prepare your code for review and submission     |
```
