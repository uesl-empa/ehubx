# Contributing to ehubX [DRAFT - to be aligned with UESL/Empa team]

Thank you for your interest in contributing to ehubX! This document outlines how you can contribute to the project.

## Repository Status: GitHub is Canonical

**Important:** This project was originally hosted on GitLab but has now migrated to GitHub. 

- **GitHub repository (the one under UESL-Empa):** https://github.com/uesl-empa/ehubx — **Primary/Canonical**
- **GitLab repository:** Legacy/archival only — **do not submit new contributions there**

All new contributions, issues, and discussions should be directed to the **GitHub repository**.

## Migrating Changes from GitLab to GitHub

If you have local changes or branches based on the GitLab repository, follow these steps to migrate your work to GitHub:

1. **Add GitHub as a remote** to your existing local repository:
   ```bash
   git remote add github https://github.com/uesl-empa/ehubx.git
   git fetch github
   ```

2. **Check your current branch** and ensure it's up to date with GitLab's main:
   ```bash
   git checkout main
   git pull origin main
   ```

3. **Rebase your work** onto GitHub's main branch:
   ```bash
   git checkout your-feature-branch
   git rebase main
   ```
   If there are conflicts, resolve them, then continue the rebase with `git rebase --continue`.

4. **Push your branch to GitHub**:
   ```bash
   git push github your-feature-branch
   ```

5. **Open a pull request** on GitHub from your branch to `main`.

**Note:** If your GitLab fork has diverged significantly, it may be easier to manually cherry-pick your commits to a fresh clone of the GitHub repository.

## Ways to Contribute

- **Reporting bugs:** Open an issue on GitHub with a clear description and steps to reproduce
- **Suggesting features:** Open an issue on GitHub to discuss new features before implementation
- **Code contributions:** Submit pull requests to the `main` branch
- **Documentation improvements:** Pull requests for documentation are always welcome
- **Examples:** Contribute new examples in the `examples/` directory

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/your-username/ehubx.git
   cd ehubx
   ```
3. Set up the development environment (see README.md for details)
4. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Pull Request Process

1. Ensure your code follows the existing style and conventions
2. Add tests for new functionality where applicable
3. Update documentation if your changes affect the API or user-facing behavior
4. Ensure all CI checks pass
5. Submit your pull request to the `main` branch
6. Reference any related issues in your pull request description

## Code Style

- Follow PEP 8 guidelines for Python code
- Use type hints where appropriate
- Include docstrings for public functions and classes
- Keep line lengths under 100 characters

## Commit Messages

Use clear, descriptive commit messages. Follow the conventional commit style:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `refactor:` for code refactoring
- `test:` for test-related changes
- `chore:` for maintenance tasks

## License

By contributing to ehubX, you agree that your contributions will be licensed under the **GNU General Public License v3.0 or later**, in line with the project's existing license.

## Questions?

If you have questions about contributing, please open an issue on GitHub or contact the maintainers.
