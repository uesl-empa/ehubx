# Contributing to ehubX [DRAFT - to be aligned with UESL/Empa team]

Thank you for your interest in contributing to ehubX! This document outlines how you can contribute to the project.

> **Draft status.** Items marked **[decide]** need a decision from the UESL/Empa
> team before they mean anything. Everything else describes how the repository
> is actually configured today.

## Repository Status: GitHub is Canonical

**Important:** This project was originally hosted on GitLab but has now migrated to GitHub.

- **GitHub repository (the one under UESL-Empa):** https://github.com/uesl-empa/ehubx — **Primary/Canonical**
- **GitLab repository:** Legacy/archival only — **do not submit new contributions there**

All new contributions, issues, and discussions should be directed to the **GitHub repository**.

---

## 1. How to contribute: which workflow applies to you

Everyone ends up at the same place — a **pull request against `main`**. Nothing
is pushed directly to `main`. How you get there depends on whether you have
write access to `uesl-empa/ehubx`.

### Internal contributors (UESL/Empa team, with write access)

Work on a **branch in the main repository**. No fork needed.

```bash
git clone https://github.com/uesl-empa/ehubx.git
cd ehubx
git checkout -b issue123_short-description
# ... work, commit ...
git push -u origin issue123_short-description
```

Then open a PR from your branch to `main`.

Why branches rather than forks: you can assign reviewers, CI has access to
repository secrets, and colleagues can push fixes to your branch during review.
None of that works from a fork.

### External contributors (no write access)

**Fork** the repository, then open a PR from your fork.

```bash
# Fork via the GitHub web UI first, then:
git clone https://github.com/your-username/ehubx.git
cd ehubx
git remote add upstream https://github.com/uesl-empa/ehubx.git
git checkout -b short-description
# ... work, commit ...
git push -u origin short-description
```

Then open a PR from `your-username/ehubx:short-description` to
`uesl-empa/ehubx:main`. **Check the base repository** — GitHub sometimes
defaults it to your own fork.

Note: contributors working from a fork **cannot assign reviewers** — GitHub only
allows that with write access. @-mention someone in a PR comment instead.

### Not sure which you are?

If you can push a branch to `uesl-empa/ehubx`, you are internal. If you get a
403, you are external — use a fork. Team members who expect write access but do
not have it should ask the maintainers.

### Sensitive or restricted work

Some work cannot simply be pushed to a public repository: unpublished methods
under embargo, industry collaborations under NDA, or projects whose grant or
contract terms specify where data and code may be hosted.

**If your work is under data-protection or contractual restrictions, consult the
maintainers before choosing where to host it.** Requirements vary by project and
some are contractual rather than technical — for example, terms that name a
jurisdiction or prohibit third-party hosting. This is not a decision to make
alone.

Two things that are true regardless:

- **Confidential input data does not belong in the repository**, public or
  private. Keep model inputs outside the repo and reference them by path.
  This is separate from whether the *code* is sensitive.
- **Long-lived private branches get expensive to merge.** If work is embargoed
  rather than permanently closed, rebase onto `main` regularly rather than
  diverging for months.

### Branch naming

Follow the convention carried over from GitLab:

```
issue<number>_<short-description>
```

for example `issue279_fix-opex-per-energy-main-carrier`. For work without an
issue, a short descriptive name is fine (`autonomy-module`, `docs/setup-guide`).

---

## 2. Setting up your development environment

### Requirements

- **Python 3.11, 3.12 or 3.13** (CI tests all three)
- **Poetry** for dependency management
- **A MILP solver** — see below

### Install

```bash
pip install poetry
poetry install
poetry run pre-commit install
```

That last command installs the repository's git hooks
(`.pre-commit-config.yaml`): ruff, ruff-format, mypy, and merge-conflict and
whitespace checks. They run automatically on every commit and are the easiest
way to avoid a red CI run.

### Installing a solver (important)

ehubX needs a MILP solver to run models. CI uses GLPK.

| Platform | Command |
|---|---|
| Linux | `sudo apt-get install glpk-utils` |
| Windows (admin) | `choco install glpk` |
| Windows (no admin) | Download [winglpk](https://sourceforge.net/projects/winglpk/), unzip, put `glpsol.exe` on your `PATH` |
| macOS | `brew install glpk` |

**Without a solver, roughly 200 tests fail on a clean checkout.** They are not
broken — they simply cannot run. If you see a large number of failures
immediately after cloning, check `glpsol --help` works before investigating
anything else.

### Running checks locally

```bash
poetry run ruff check src --ignore C901
poetry run mypy src
poetry run pytest
```

CI runs exactly these across Python 3.11, 3.12 and 3.13. The release and
publish jobs are gated to `release` and `workflow_dispatch` events, so they
show as **skipped** on pull requests — that is expected, not a failure.

---

## 3. Rules for commits

### Commit messages

Explain **why**, not just what — the diff already shows what changed. A subject
line under ~72 characters, a blank line, then the reasoning.

Separate unrelated changes into separate commits, even within one PR. This
matters more than it sounds: it is what lets a behaviour change be reverted
later without unpicking everything around it.

**[decide]** — whether to adopt conventional commit prefixes (`feat:`, `fix:`,
`docs:`, `refactor:`, `test:`, `chore:`). No commit in the repository currently
uses them, so this would be a new convention rather than a description of
existing practice.

### Code style

- **Line length: 88 characters** — enforced by ruff, configured in
  `pyproject.toml`. Do not use 100.
- Follow PEP 8; ruff-format handles most of it automatically
- Use type hints — mypy runs in CI
- Include docstrings for public functions and classes

### Porting a commit from GitLab

The two repositories share **no common history**, so a GitLab branch cannot be
merged into this one. Port the content as a patch, and record provenance with
git trailers so it survives the GitLab archive:

```
GitLab-Commit: <full 40-character sha>
GitLab-URL: https://gitlab.empa.ch/ues-lab/team-mes/ehub-modelling/ehubX/-/commit/<sha>
```

Credit the original author with `Co-Authored-By:` if the work is not yours.
`MIGRATION_AUDIT.md` documents the 2026 port and is a worked example.

---

## 4. Pull request process

1. Ensure your code follows the existing style and conventions
2. Add tests for new functionality where applicable
3. Update documentation if your changes affect the API or user-facing behavior
4. Ensure all CI checks pass
5. Submit your pull request to the `main` branch
6. Reference any related issues in your pull request description

### Review

Every PR needs at least one approving review before merge. **[decide]** —
number of approvals, and whether this is enforced by branch protection.

When you push new commits to an open PR, the PR updates automatically and CI
reruns. Prefer follow-up commits over force-pushes once review has started: a
force-push can detach existing review comments from the lines they refer to.

**[decide]** — squash policy. If a PR has deliberately separated commits, say so
in the description and ask not to squash; otherwise squash-merge keeps `main`
tidy.

### Changes that affect results

ehubX produces numbers that people publish. Some changes are not just code
changes:

- **Changing a constraint or cost term** alters objective values. Say so
  explicitly in the PR description, and say which model configurations are
  affected.
- **Changing an `ENTRY_` label or output filename** in `src/ehubx/writer/`
  changes result files. Downstream scripts parse these. Call it out.
- **Adding a model parameter** is usually safe: result CSVs use a fixed column
  schema (`DfStColumn` in `writer/common_writer.py`) and parameters are written
  as rows, so new parameters do not add columns.

If you are unsure whether a change is result-affecting, assume it is and mention
it. A reviewer would much rather read one unnecessary paragraph than discover it
after a paper is submitted.

---

## 5. Migrating existing work from GitLab

If you have local changes or branches based on the GitLab repository:

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

**Note:** the two repositories share no common history, so a rebase may not be
possible — `git merge-base` finds nothing between them. If your branch has
diverged significantly, cherry-pick your commits onto a fresh clone of the
GitHub repository instead, and record provenance with the `GitLab-Commit:`
trailers described above.

---

## Ways to Contribute

- **Reporting bugs:** Open an issue on GitHub with a clear description and steps to reproduce
- **Suggesting features:** Open an issue on GitHub to discuss new features before implementation
- **Code contributions:** Submit pull requests to the `main` branch
- **Documentation improvements:** Pull requests for documentation are always welcome
- **Examples:** Contribute new examples in the `examples/` directory

A good bug report includes the ehubX version, Python version, solver, a minimal
input that reproduces the problem, and what you expected instead. If the model
is confidential, describe its shape rather than attaching it.

## Versioning and releases

The project follows [SemVer](https://semver.org/):

- **MAJOR** — breaks existing models or output-file structure
- **MINOR** — new capability, existing models unaffected
- **PATCH** — bug fix with no interface change

**Do not bump the version in a feature PR.** Version bumps belong to a release
commit, which changes three files together or the package misreports itself:

```
pyproject.toml          version = "X.Y.Z"
src/ehubx/__init__.py   __version__ = "X.Y.Z"
docs/source/conf.py     release = "X.Y.Z"
```

Then add a `CHANGELOG.rst` entry and publish a GitHub Release tagged `X.Y.Z`
(bare tag, no `v` prefix) — the `publish_pypi` job triggers on
`release: published`.

> **PyPI is write-once.** Once a version is uploaded it can never be replaced,
> even after deletion. Test first via **Actions → CI → Run workflow** with
> `publish_target: testpypi`.

## License

By contributing to ehubX, you agree that your contributions will be licensed under the **GNU General Public License v3.0 or later**, in line with the project's existing license.

## Questions?

If you have questions about contributing, please open an issue on GitHub or contact the maintainers. If this document is wrong or unclear, that is a bug in the document — please fix it.
