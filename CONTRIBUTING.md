# Contributing to ehubX [DRAFT - to be aligned with UESL/Empa team]

Thank you for your interest in contributing to ehubX!

This document has two parts:

- **[Part A — How we work](#part-a--how-we-work)** describes the process: who
  does what, in which order, and why. No programming knowledge is needed to
  follow it.
- **[Part B — Technical reference](#part-b--technical-reference)** gives the
  commands and set-up details for each step. Part A links to the right place.

> **Draft status.** Items marked **[decide]** need a decision from the UESL/Empa
> team before they mean anything. Everything else describes how the repository
> is actually configured today.

---

# Part A — How we work

## A1. Where the project lives

The project moved from GitLab to GitHub in 2026.

- **GitHub** — https://github.com/uesl-empa/ehubx — is the **only** place for
  new work, issues and discussions.
- **GitLab** is legacy and archival only. **Do not submit new contributions
  there.**

## A2. Roles

Most people are **model users**: they run ehubX for their own studies and
never change its code. That is the most common way to take part, and reporting
problems is a real contribution.

| Role | Who | Responsible for |
|---|---|---|
| **Model user** | Anyone who runs ehubX for their work | Reporting bugs, unclear documentation and unexpected results as issues; suggesting features. No code changes, no git needed. See [A9](#a9-reporting-problems-and-other-ways-to-contribute). |
| **Contributor** | Anyone making a change to the code or documentation | Doing the work, opening the pull request, responding to review |
| **Reviewer** | A team member other than the contributor | Checking the change is correct and that its effect on results is understood; approving or requesting changes |
| **Maintainer** | **[decide]** — named people in the UESL/Empa team | Granting write access, merging **[decide]**, publishing releases, deciding where sensitive work is hosted |

## A3. The workflow, step by step

### For model users

You do **not** need a fork, git, or a GitHub copy of the project to use
ehubX. A fork is only for proposing changes back to the project; if you only
run the model, it would just be an extra copy that falls out of date.

| # | Step | What it involves |
|---|---|---|
| 1 | **Install ehubX** | Install the published package and a solver. See [B1](#b1-setting-up-your-environment). |
| 2 | **Keep your model inputs in your own folder** | Your input files and results belong to your study, not to the ehubX project. Keep them outside the ehubX code, and back them up or version them however suits your project. See [A6](#a6-sensitive-or-restricted-work) for confidential data. |
| 3 | **Record which version you used** | Note the ehubX version for every study, so results can be reproduced later. |
| 4 | **Upgrade deliberately** | Before upgrading mid-study, read the changelog: a new version can change results (see [A5](#a5-changes-that-affect-results)). |
| 5 | **Report problems** | Open an issue on GitHub. See [A9](#a9-reporting-problems-and-other-ways-to-contribute). |

If you want to fix something yourself, you become a contributor and follow the
workflow below. Only then may you need a fork (see [A4](#a4-internal-or-external-contributor)).

### For contributors

Every change — a bug fix, a new model feature, a documentation correction —
follows the same path and ends as a **pull request** (PR) into the `main`
branch. Nobody changes `main` directly.

| # | Step | Who | What it involves |
|---|---|---|---|
| 1 | **Raise an issue** | Anyone, often a model user | Describe the bug or the feature on GitHub. For anything larger than a small fix, discuss it before starting, so nobody works in parallel on the same thing. A model user's part usually ends here, apart from answering questions on the issue. |
| 2 | **Create a working branch** | Contributor | A private copy of the code to work in, named after the issue. See [B2](#b2-day-to-day-git-commands) and [B3](#b3-branch-naming). |
| 3 | **Make the change** | Contributor | Include tests for new functionality, and update the documentation if users will notice the change. Keep unrelated changes apart. |
| 4 | **Check it locally** | Contributor | Run the automatic checks on your own machine before asking anyone to look. See [B4](#b4-running-the-checks). |
| 5 | **Open a pull request** | Contributor | Explain *why* the change is needed, link the issue, and **state whether it changes model results** (see [A5](#a5-changes-that-affect-results)). |
| 6 | **Review** | Reviewer | At least one approving review is needed. **[decide]** — number of approvals, and whether this is enforced automatically. |
| 7 | **Respond to review** | Contributor | Make the requested changes. The pull request updates itself, and the automatic checks run again. |
| 8 | **Merge** | **[decide]** — contributor after approval, or maintainer | The change enters `main`. **[decide]** — squash policy; see [B6](#b6-merging). |
| 9 | **Release** | Maintainer | Bundling merged changes into a new published version. See [A7](#a7-versions-and-releases). |

## A4. Internal or external contributor?

Both end with a pull request into `main`; the route differs.

- **Internal contributors** (UESL/Empa team, with write access) work on a
  branch **inside** the main repository. This lets you assign reviewers, lets
  the automatic checks use repository settings, and lets colleagues push fixes
  to your branch during review.
- **External contributors** (no write access) work in their own copy of the
  repository, called a **fork**, and open the pull request from there. From a
  fork you **cannot assign reviewers** — mention someone by `@name` in a
  comment instead.

**Not sure which you are?** If you can push a branch to `uesl-empa/ehubx`, you
are internal. If you are refused, you are external. Team members who expect
write access but do not have it should ask a maintainer.

Commands for both routes: [B2](#b2-day-to-day-git-commands).

## A5. Changes that affect results

ehubX produces numbers that people publish. Some changes are not just code
changes, and the pull request must say so:

- **Changing a constraint or cost term** alters objective values. Say so
  explicitly, and say which model configurations are affected.
- **Changing an output label or output filename** changes result files.
  Downstream scripts read these. Call it out.
- **Adding a model parameter** is usually safe: result files have a fixed
  column layout and parameters are written as rows, so new parameters do not
  add columns.

If you are unsure whether a change affects results, assume it does and mention
it. A reviewer would much rather read one unnecessary paragraph than discover it
after a paper is submitted.

## A6. Sensitive or restricted work

Some work cannot simply be published: unpublished methods under embargo,
industry collaborations under NDA, or projects whose grant or contract terms
specify where data and code may be hosted.

**If your work is under data-protection or contractual restrictions, consult the
maintainers before choosing where to host it.** Requirements vary by project and
some are contractual rather than technical — for example, terms that name a
jurisdiction or prohibit third-party hosting. This is not a decision to make
alone.

Two things are true regardless:

- **Confidential input data does not belong in the repository**, public or
  private. Keep model inputs outside the repository and refer to them by path.
  This is separate from whether the *code* is sensitive.
- **Long-lived private branches get expensive to merge.** If work is embargoed
  rather than permanently closed, bring it up to date with `main` regularly
  rather than letting it drift apart for months.

## A7. Versions and releases

The project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** — breaks existing models or the structure of output files
- **MINOR** — new capability; existing models unaffected
- **PATCH** — bug fix with no change to how the model is used

**Contributors do not change the version number.** Releases are done by a
maintainer as a separate step. Procedure: [B8](#b8-release-procedure).

## A8. Moving work from GitLab

If you still have work that only exists on GitLab:

1. **Check it is not already on GitHub.** Much of GitLab `main` was ported in
   2026; `MIGRATION_AUDIT.md` lists what was moved and what was not.
2. **Bring it across as a new pull request** on GitHub, following the workflow
   in [A3](#a3-the-workflow-step-by-step).
3. **Credit the original author** if the work is not yours, and **record where
   it came from** on GitLab, so the history survives once GitLab is archived.

The two repositories do not share history, so this is a copy rather than a
simple transfer. How to do it: [B7](#b7-moving-work-from-gitlab).

## A9. Reporting problems and other ways to contribute

For model users, issues are the main way to take part. Open one when:

- the model crashes or gives an error you cannot explain
- results look wrong or change unexpectedly between versions
- the documentation is missing, unclear or does not match the model
- a feature you need is missing

You need a free GitHub account, and nothing else.

Other ways to contribute:

- **Reporting bugs** — open an issue with a clear description and steps to
  reproduce
- **Suggesting features** — open an issue to discuss before anyone starts work
- **Improving documentation** — always welcome
- **Examples** — new example models in the `examples/` folder

A good bug report includes the ehubX version, Python version, solver, a minimal
input that reproduces the problem, and what you expected instead. If the model
is confidential, describe its shape rather than attaching it.

---

# Part B — Technical reference

## B1. Setting up your environment

### For model users

Install the published package from [PyPI](https://pypi.org/project/ehubx/),
ideally in its own Python environment:

```bash
pip install ehubx               # latest version
pip install ehubx==2.3.1        # a specific version, e.g. to reproduce a study
```

You also need a solver; see [Installing a solver](#installing-a-solver-important)
below.

Check which version you have (include this in bug reports):

```bash
pip show ehubx
```

Upgrade when you are ready, after reading `CHANGELOG.rst`:

```bash
pip install --upgrade ehubx
```

The example models are in the
[`examples/`](https://github.com/uesl-empa/ehubx/tree/main/examples) folder on
GitHub. Download them with **Code → Download ZIP**; no git is needed.

### For contributors: requirements

- **Python 3.11, 3.12 or 3.13** (the automatic checks test all three)
- **Poetry** for dependency management
- **A MILP solver** — see below

### For contributors: install

```bash
git clone https://github.com/uesl-empa/ehubx.git
cd ehubx
pip install poetry
poetry install
poetry run pre-commit install
```

The last command installs the repository's git hooks
(`.pre-commit-config.yaml`): ruff, ruff-format, mypy, and merge-conflict and
whitespace checks. They run automatically on every commit and are the easiest
way to avoid a failed CI run.

If you use your own environment (for example conda) instead of Poetry, install
ehubX in **editable** mode from the repository folder:

```bash
pip install -e .
```

Otherwise Python may import an older installed copy of ehubX instead of the
code you are editing, and your tests check the wrong code without any warning.

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

## B2. Day-to-day git commands

### Internal contributors (branch in the main repository)

```bash
git clone https://github.com/uesl-empa/ehubx.git
cd ehubx
git checkout -b issue123_short-description
# ... work, commit ...
git push -u origin issue123_short-description
```

Then open a pull request from your branch to `main` on GitHub.

### External contributors (fork)

```bash
# Fork via the GitHub web UI first, then:
git clone https://github.com/your-username/ehubx.git
cd ehubx
git remote add upstream https://github.com/uesl-empa/ehubx.git
git checkout -b short-description
# ... work, commit ...
git push -u origin short-description
```

Then open a pull request from `your-username/ehubx:short-description` to
`uesl-empa/ehubx:main`. **Check the base repository** — GitHub sometimes
defaults it to your own fork.

### Updating a pull request during review

Push new commits to the same branch; the pull request updates and CI reruns.
Prefer follow-up commits over force-pushes once review has started: a
force-push can detach existing review comments from the lines they refer to.

## B3. Branch naming

Follow the convention carried over from GitLab:

```
issue<number>_<short-description>
```

for example `issue279_fix-opex-per-energy-main-carrier`. For work without an
issue, a short descriptive name is fine (`autonomy-module`, `docs/setup-guide`).

## B4. Running the checks

```bash
poetry run ruff check src --ignore C901
poetry run mypy src
poetry run pytest
```

CI runs exactly these across Python 3.11, 3.12 and 3.13. The release and
publish jobs are gated to `release` and `workflow_dispatch` events, so they
show as **skipped** on pull requests — that is expected, not a failure.

On Windows, if many tests fail at setup with `PermissionError` in
`AppData\Local\Temp`, pytest cannot write its temporary folder. Point it at one
it can write to:

```bash
poetry run pytest --basetemp=<a folder you can write to>
```

## B5. Commit and code rules

### Commit messages

Explain **why**, not just what — the diff already shows what changed. A subject
line under ~72 characters, a blank line, then the reasoning.

Separate unrelated changes into separate commits, even within one pull request.
This matters more than it sounds: it is what lets a behaviour change be
reverted later without unpicking everything around it.

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

### Output labels

Output labels are the `ENTRY_` constants and output filenames in
`src/ehubx/writer/`. Changing them is result-affecting (see
[A5](#a5-changes-that-affect-results)). Result CSVs use a fixed column schema
(`DfStColumn` in `writer/common_writer.py`), which is why new parameters add
rows rather than columns.

## B6. Merging

**[decide]** — squash policy. If a pull request has deliberately separated
commits, say so in the description and ask not to squash; otherwise
squash-merge keeps `main` tidy.

**Branches built on other branches.** If your branch started from another
feature branch rather than `main`, and that other branch was later
squash-merged, git can no longer recognise its commits as already merged. Your
branch then appears to carry them again, and merging reports conflicts that
are not real. Replay only your own commits onto `main`:

```bash
git fetch origin
git rebase --onto origin/main <last-commit-of-the-other-branch> <your-branch>
```

## B7. Moving work from GitLab

The two repositories share **no common history** — `git merge-base` finds
nothing between them — so a GitLab branch cannot be merged or simply rebased
into this one. Port the content as a patch or cherry-pick onto a fresh clone
of the GitHub repository:

```bash
git remote add github https://github.com/uesl-empa/ehubx.git
git fetch github
git checkout -b your-feature-branch github/main
git cherry-pick <gitlab-commit>        # repeat per commit, resolve conflicts
git push github your-feature-branch
```

Record provenance with git trailers in each commit message, so it survives the
GitLab archive:

```
GitLab-Commit: <full 40-character sha>
GitLab-URL: https://gitlab.empa.ch/ues-lab/team-mes/ehub-modelling/ehubX/-/commit/<sha>
```

Credit the original author with `Co-Authored-By:` if the work is not yours.
`MIGRATION_AUDIT.md` documents the 2026 port and is a worked example.

## B8. Release procedure

For maintainers. A version bump is its own release commit, which changes three
files together or the package misreports itself:

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

---

## License

By contributing to ehubX, you agree that your contributions will be licensed
under the **GNU General Public License v3.0 or later**, in line with the
project's existing license.

## Questions?

If you have questions about contributing, please open an issue on GitHub or
contact the maintainers. If this document is wrong or unclear, that is a bug in
the document — please fix it.
