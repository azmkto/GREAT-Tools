# Updating `great`

For collaborators. Two different things are called "updating", and you will do both:

- **[Getting someone else's changes](#1-getting-the-latest)** — keeping your copy current.
- **[Making a change yourself](#2-making-a-change)** — fixing a bug, adding a function.

New here? Do [day one](#0-day-one) first. Installing is covered in
[TUTORIAL.md §1](TUTORIAL.md); this file assumes it is already done.

---

## Quick reference

| I want to… | Do this |
|---|---|
| Get the latest, working locally | `git pull` — that's all, no reinstall |
| Get the latest, on a Colab runtime | Reinstall from GitHub, then **restart the runtime** |
| Fix or add something | Branch → commit → push → Pull Request → review → merge |
| Know if my change belongs in the library | [§2.1](#21-does-it-belong-here) |
| Check I did not break anything | [§2.5](#25-test-before-you-push) |
| Edit a notebook | Read [§3.1](#31-notebook-conflicts) first — seriously |
| Add a new dependency | [§3.2](#32-dependencies-and-extras) — the wrong extra breaks everyone |

---

## 0. Day one

1. Accept the emailed repository invitation. The repo is public, so anyone can clone it, but
   you need the invitation to push branches.
2. Clone and install:
   ```bash
   git clone https://github.com/azmkto/GREAT-Tools.git
   cd GREAT-Tools
   py -3.11 -m pip install -e ".[all]"
   ```
3. Set your identity so reviewers know whose commit is whose:
   ```bash
   git config user.name "Your Name"
   git config user.email "you@example.com"
   ```
4. Prove it worked — run this **from a directory that is not the clone**, because being
   importable from anywhere is the whole point:
   ```bash
   py -3.11 -c "from great import sent_colors; from great.viz import weekly_overview; print(sent_colors)"
   ```
   If it prints the palette, you are set. If you get `ModuleNotFoundError`, your Jupyter kernel
   is a different Python than the one you installed into — see TUTORIAL.md §1a.
5. Skim [TUTORIAL.md §2 and §3](TUTORIAL.md) so you know what already exists. Adding a second
   version of something the library already has is the most common wasted effort here.

---

## 1. Getting the latest

### Working locally

```bash
git pull
```

That is the entire procedure. Because you installed with `pip install -e`, your Python points
straight at the clone — pulling new commits updates the library in place. There is no
reinstall step.

Two exceptions:

- **Restart your kernel.** Python imports a module once per process, so a notebook that
  already ran `import great` keeps the old code until you restart it — or use
  `%load_ext autoreload` / `%autoreload 2` at the top of the notebook to pick up edits live.
- **Re-run the install if dependencies changed.** If someone added a library to
  `pyproject.toml`, `git pull` does not install it. Re-run
  `py -3.11 -m pip install -e ".[all]"` — it is quick and safe to repeat.

See what you just received:

```bash
git log --oneline -10          # what changed
git log -p -- great/           # the actual diffs to library code
```

### On a Colab runtime (browser Colab, or VS Code attached to Colab)

The runtime installed a *snapshot* from GitHub, so it will not see new commits on its own:

```python
%pip install -q --upgrade --force-reinstall --no-deps "great[all] @ git+https://github.com/azmkto/GREAT-Tools.git"
```

Then **restart the runtime** — `--force-reinstall` replaces the files, but the already-imported
module stays in memory until you do.

If you cloned into `/content` instead (TUTORIAL.md §1b), just `!git -C /content/great pull`.

### Something broke after pulling

Someone probably changed behaviour you depended on. Check the recent commits and the PR that
introduced it, then either adapt your notebook or pin a known-good version while you do:

```python
%pip install -q "great[all] @ git+https://github.com/azmkto/GREAT-Tools.git@v0.1.0"
```

Say something in the repo's Issues. If a change broke your work it will break someone else's.

---

## 2. Making a change

### 2.1 Does it belong here?

**Yes** when a *second* notebook needs the same thing. That is the whole rule. `great.viz` and
`great.viz.wordcloud` both exist because two notebooks had byte-identical copies of them.

**Yes** for anything that is a shared vocabulary: a label list, a color, a stopword set, a
cleaning rule. Those drifting between notebooks is what the library was built to stop.

**No** for one-off analysis, anything that only makes sense inside one notebook's flow, and
anything interactive — no `input()`, no `st.*`. Library functions take arguments and return
values.

If you are unsure, open an Issue and ask before writing it.

### 2.2 The loop

Never commit to `main` directly. One branch per change, reviewed by someone else, merged
through a Pull Request. That single rule is what keeps this library from rotting back into
copy-paste.

```bash
git pull                              # start from current main
git checkout -b fix-date-parsing      # one branch, one concern
#   ...edit, test (§2.5)...
git add -A
git commit -m "Parse dates as ISO8601 so pandas 3 stops swapping day and month"
git push -u origin fix-date-parsing
```

Then open a Pull Request on GitHub, get a review, merge, and delete the branch.

**Branch names** — a prefix and a few words: `fix-`, `add-`, `docs-`, `refactor-`.
For example `add-emotion-palette`, `docs-colab-setup`.

**Commit messages** — say *why*, not *what*; the diff already shows what.
"Parse dates as ISO8601 so pandas 3 stops swapping day and month" tells the next person
something real. "Update prep.py" tells them nothing.

**If `main` moved while you were working:**

```bash
git pull --rebase origin main
```

Rebase keeps history linear. One caveat: do not rebase a branch someone else has already
pulled — it rewrites commits they already have. If you are sharing a branch, use
`git merge origin/main` instead.

### 2.3 Writing the code

Match what is already there. The specific things that matter in this package:

**Every input is a parameter.** In a notebook everything is global, so a function can read a
variable it was never passed and still work. Moved into a module, the same function raises
`NameError`. Three functions here did exactly that — `plot_sentiment_platform_overview` read
`ps_data`, `plat_data` and `sent_data` off the notebook's globals. If your function uses a
name, it must have received it.

**Keep the core importable without heavy dependencies.** `import great` must not pull in
matplotlib, scikit-learn or wordcloud. That is why `great.text` and `great.viz` are not
re-exported from `great/__init__.py`, and why `great.text` imports `ftfy`/`nltk`/`Sastrawi`
lazily inside its functions rather than at module level. Preserve that.

**Docstrings explain *why*, not *what*.** The signature already says what. Write a line when
there is a non-obvious reason — a default that looks arbitrary, a rule that surprised you.
`distinctive_terms()` documenting why it drops unigrams covered by a bigram is the useful
kind.

**Do not silently change existing behaviour.** If you refactor, the numbers should come out
identical — see §2.5.

### 2.4 Where things go

| Adding… | Goes in |
|---|---|
| A label list, platform name, category | `great/labels.py` |
| A color or plot-size constant | `great/palette.py` |
| An export column or validation rule | `great/schema.py` |
| A text cleaner, slang or stopword | `great/text.py` |
| A data-reshaping step | `great/viz/prep.py` |
| A load-time sanity report | `great/viz/checks.py` |
| A figure | `great/viz/overview.py` or a new module under `great/viz/` |

New module under `great/viz/`? Import it in `great/viz/__init__.py` and add it to `__all__`, so
one import gets the whole toolkit. Add the module to the reference table in TUTORIAL.md §3.

### 2.5 Test before you push

There is no automated test suite, so these are the checks.

```bash
# 1. Everything imports, from OUTSIDE the clone
cd /
py -3.11 -c "import great; from great.viz import prep, checks, wordcloud, weekly_overview, monthly_overview; print('ok')"

# 2. The core stays lightweight - must print: False False False
py -3.11 -c "import sys, great; print('matplotlib' in sys.modules, 'sklearn' in sys.modules, 'wordcloud' in sys.modules)"
```

Then re-run both example notebooks end to end — they are the closest thing to an integration
test — and confirm zero errors:

```bash
py -3.11 -c "import nbformat; from nbclient import NotebookClient; [NotebookClient(nbformat.read(p, as_version=4), timeout=1800, kernel_name='python3').execute() for p in [r'Weekly Visualization\example_weekly_with_great.ipynb', r'Monthly Visualization\example_monthly_with_great.ipynb']]; print('both notebooks ran clean')"
```

**If your change was meant to change nothing, prove it changed nothing.** Note the
`sent_pct_df` and `platform_totals_df` values before your change, and compare after. A
refactor that quietly moves a percentage is worse than no refactor.

### 2.6 Opening the Pull Request

Say in the description:

- **What and why** — the problem, not just the change.
- **Whether behaviour changed** for anyone's existing notebooks. If yes, spell out what they
  need to do.
- **What you tested** — which of §2.5's checks you ran.
- **If you edited a notebook**, say which one (see §3.1).

Then ask someone to review it. Small PRs get reviewed; large ones sit.

### 2.7 Reviewing someone else's PR

Beyond "does it work", these four are the failure modes this package has actually hit:

1. **Does the code read a name it never received as a parameter?** See §2.3.
2. **Is a new dependency in the right extra?** See §3.2. This one breaks everyone, silently.
3. **Does it belong in the library at all?** See §2.1.
4. **Does it change results for existing notebooks?** If yes, it needs a version bump and a
   clear note — see §3.3.

Approve, or ask for changes. Reviewing is not gatekeeping; it is the only reason this stays
usable by more than one person.

### 2.8 After it merges

Delete the branch. Tell the team if it affects their work. Everyone else picks it up with
`git pull`.

---

## 3. The traps

These three cause almost every problem in this repo. Read them once now, not later.

### 3.1 Notebook conflicts

The notebooks here keep their outputs, including embedded figures. That makes them megabytes
of base64, and **git cannot merge two people's edits to the same notebook.** You will get a
conflict that cannot be resolved by hand.

- **One person owns a notebook at a time.** Say you are editing it before you start.
- **Never hand-merge notebook JSON.** If you hit a conflict, take one side whole and re-run:
  ```bash
  git checkout --theirs "Monthly Visualization/example_monthly_with_great.ipynb"
  # or --ours to keep your version
  ```
  then re-execute the notebook top to bottom and commit the result.
- **Prefer changing the library over the notebook.** Python files in `great/` merge cleanly.
  Notebooks do not. This is the same instinct as §2.1, with a second reason behind it.

The two archived notebooks — `pol_weekly_viz.ipynb` and `pol_monthly_viz.ipynb` — are the
historical record and should not be edited at all. Their stored outputs are the *only* correct
copy: they still contain the original `dayfirst=True` date parsing, so re-running them today
produces wrong dates (TUTORIAL.md §6).

### 3.2 Dependencies and extras

`pyproject.toml` splits optional dependencies into `text`, `ml`, `viz` and `all`. Put a new
dependency in the extra that matches the module using it.

**The trap:** anything imported at **module level** under `great/viz/` must be reachable from
the `viz` extra, or `from great.viz import prep` breaks for everyone — including people who
never touch the module you added. This happened when `scikit-learn` was moved into its own
`ml` extra while `great/viz/wordcloud.py` still imported `TfidfVectorizer` at import time.
`viz` now includes `great[ml]` for exactly that reason.

After changing `pyproject.toml`, run check 2 in §2.5 and confirm `import great` still needs
nothing heavy.

### 3.3 Breaking changes

Everyone's notebooks import the same package, so renaming or removing a function breaks their
work silently at their next `git pull`. Prefer adding a new function over changing an existing
one. Deprecate rather than delete. When it is unavoidable:

1. Say so plainly in the PR, including what to rename.
2. Bump `version` in `pyproject.toml`.
3. Tag it, so old notebooks can pin a known-good version:
   ```bash
   git tag v0.2.0
   git push --tags
   ```

TUTORIAL.md §4 has the pinned-install syntax.

---

## 4. Never commit

- **Data exports.** `.gitignore` blocks `*.xlsx`, `*.xls`, `*.csv` and `*.zip`. Keep it that
  way — the exports contain real mention text and author names, and they are large.
- **Tokens, of any kind** (GitHub, Hugging Face, API keys). Not in a cell, not in a file, not
  in a commit message. If one leaks, revoke it immediately — deleting the commit is not enough,
  because it stays in the history and in every clone anyone has already made.
- **Notebook outputs you would not publish.** Outputs are committed with the notebook, so a
  printed dataframe or a topic table is as public as the code. Clear outputs (Edit → Clear All
  Outputs) before committing if they show mention text, author names, or client findings.
- **Virtualenvs and build artifacts.** Also gitignored.

This repo is public. Anyone on the internet can read every file and every past commit.
