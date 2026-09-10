# great — Tutorial

`great` is the shared library for this portfolio: label vocabularies, color palette,
text cleaning, environmental-issue rules, and province geography that used to be
copy-pasted across `Evolution Project`, `Topic Modelling Trial`, `IHSG Narratives`,
and `Weekly Monthly Visualization Program`. This doc covers installing it, using it,
and keeping it up to date.

Import name: `great` (e.g. `from great import sent_colors`)
Repo: `github.com/<owner>/great` — private, see §1d for access

---

## 1. Install

`great` is installed *from the repo*, never copied into a project. Which install command you
use depends on **where your Python actually runs** — and that is the thing people get wrong,
because two of the three setups below look identical in the editor.

| | Environment | Notebook file lives | Python runs on | How `great` is installed | Updating |
|---|---|---|---|---|---|
| §1a | Local VS Code / Jupyter | your disk | **your disk** | `pip install -e` from your clone | `git pull` |
| §1b | VS Code + Colab extension | your disk | **Google's cloud VM** | `%pip install` in a cell | reinstall + restart kernel |
| §1c | Colab (browser) | Google Drive | **Google's cloud VM** | `%pip install` in a cell | reinstall + restart runtime |

Not sure which one you are in? Run this in the notebook — it settles it in two lines:

```python
import sys, pathlib
print(sys.executable)
print('cloud runtime' if pathlib.Path('/content').exists() else 'local interpreter')
```

### 1a. Local — VS Code / Jupyter on your own machine

Clone once, then install from the clone:

```bash
git clone https://github.com/<owner>/great.git
cd great
py -3.11 -m pip install -e ".[all]"
```

Use **Python 3.11 or newer**. (`py -3.11` is the Windows launcher; on macOS/Linux use
`python3.11 -m pip ...`. On the maintainer's machine there are three Python installs and only
the 3.11 one has a working scientific stack — the Anaconda 3.9 there cannot even
`import numpy` — which is why the version is named explicitly rather than left to `python`.)

**What `-e` means.** An editable install copies nothing. It points your Python environment
straight at your clone, so editing a file under `great/` changes what every notebook sees —
after a kernel restart, or live if you use `%autoreload` (§4). It also means **`git pull` is
the entire update procedure**; there is no reinstall step.

**What `[all]` means.** Optional dependencies are split into extras:

| Extra | Pulls | Needed for |
|---|---|---|
| `text` | `ftfy`, `nltk`, `PySastrawi` | the `great.text` cleaners |
| `ml` | `scikit-learn` | the TF-IDF behind the word cloud |
| `viz` | `matplotlib`, `scienceplots`, `wordcloud`, `seaborn`, `plotly`, plus `ml` | all of `great.viz` |
| `all` | everything above | everything |

`great.viz` imports its dependencies at module level, so `[viz]` is not optional if you want
plots — even `from great.viz import prep` fails without it. Plain `import great` needs none of
them, so a text-only or headless environment can install the bare package.

**Check it worked** — run this from a directory that is *not* the clone, which is the whole
point of installing rather than copying:

```bash
py -3.11 -c "from great import sent_colors; from great.viz import weekly_overview; print(sent_colors)"
```

If that prints the palette, `great` is importable from any notebook anywhere on your machine.

**`ModuleNotFoundError` after installing?** Your Jupyter kernel is almost certainly a different
Python than the one you installed into. Check which one it is, and compare it against the
interpreter you ran `pip` with:

```python
import sys; print(sys.executable)
```

### 1b. VS Code + the Colab extension

Google's official Colab extension (shipped November 2025) lets you keep editing notebooks in
VS Code while the code runs on a Colab runtime, including Pro GPU/TPU machines.

**Connecting:**

1. Extensions view (`Ctrl+Shift+X`) → search **"Google Colab"** → Install. It will also install
   the Jupyter extension if you do not have it.
2. Open any `.ipynb` in your workspace.
3. Click **Select Kernel** (top right), choose **Colab**, sign in with your Google account,
   and pick a runtime.

**Read this before anything else.** Your notebook file is on your disk, but the kernel is a
virtual machine in Google's cloud. That means:

- Your local editable install from §1a is **invisible** here. `import great` will fail until
  you install it *into the runtime*.
- Editing `great/viz/prep.py` in the same VS Code window changes **nothing** in the runtime.
- The runtime cannot read your local data files.

Because the file sits right there in your editor, this setup *feels* local. That is exactly
why people lose an hour to it. Run the environment check at the top of §1 if in doubt.

**Getting `great` into the runtime.** Pick based on whether you intend to edit the library
during this session.

*Just using it* — one cell near the top of the notebook:

```python
import getpass
token = getpass.getpass('GitHub PAT: ')    # paste at the prompt, never into a cell
%pip install -q "great[all] @ git+https://{token}@github.com/<owner>/great.git"
```

`getpass` keeps the token out of the saved `.ipynb` and out of cell output. See §1d for
creating a fine-grained, read-only PAT.

> **Token hygiene.** A *failed* pip install can echo the full URL — token included — in its
> error text. If that ever lands in a notebook you share, revoke the token and issue a new one.
> Colab Secrets (`google.colab.userdata`) is a feature of the Colab browser UI; whether it is
> reachable from the VS Code extension is unverified, so `getpass` is the reliable path here.

*Also editing the library* — clone into the runtime and install editable, so `!git pull`
updates it with no reinstall:

```python
import getpass
token = getpass.getpass('GitHub PAT: ')
!git clone -q https://{token}@github.com/<owner>/great.git /content/great
%pip install -q -e "/content/great[all]"
```

```python
%load_ext autoreload
%autoreload 2
```

Now edits to files under `/content/great` take effect live, and you can commit and push from
the runtime like any other clone (`!git -C /content/great add -A`, and so on).

**After installing**, restart the kernel if you had already imported `great` this session —
the restart button in the notebook toolbar. Then verify:

```python
import great
from great.viz import weekly_overview
print(great.__version__, great.__file__)
```

`great.__file__` should point somewhere under `/usr/local/lib/` or `/content/great`, **not**
at a Windows path. If it shows a Windows path, you are on a local kernel, not a Colab one.

**Getting your data there.** The runtime cannot see your local disk, so the `DATA` path in the
example notebooks will not resolve. Either mount Drive:

```python
from google.colab import drive
drive.mount('/content/drive')
DATA = '/content/drive/MyDrive/<your data folder>'
```

or upload for the session only:

```python
from google.colab import files
files.upload()
```

### 1c. Google Colab (browser)

A fresh VM every session, with no view of your machine — so `great` comes from GitHub, not a
local path. Add this as the *first* cell:

```python
from google.colab import userdata
token = userdata.get('GH_TOKEN')
%pip install -q "great[all] @ git+https://{token}@github.com/<owner>/great.git"
```

Store the token in the Colab Secrets panel (key icon, left sidebar) as `GH_TOKEN` — see §1d.
If the repo were public, the token part drops out entirely:

```python
%pip install -q "great[all] @ git+https://github.com/<owner>/great.git"
```

Colab installed a *snapshot*, so it will not see new commits on its own. To update, reinstall
with `--force-reinstall --no-deps` and then **Restart runtime** (§4).

### 1d. Team access to a private repo

Nothing about the package or the install commands changes for a teammate — only *how they
authenticate*. Two cases:

**Local (§1a) — no token needed at all.** Once someone is added as a Collaborator, their normal
`git clone`, using whatever SSH key or credential manager they already have configured with
GitHub, just works:

```bash
git clone git@github.com:<owner>/great.git      # or the https:// URL with a credential manager
cd great
py -3.11 -m pip install -e ".[all]"
```

**Any cloud runtime (§1b and §1c) — each person needs their own token.** A Colab VM has no
persistent SSH key, so it authenticates over HTTPS with a credential in the URL:

1. Each person creates their own **fine-grained personal access token**, scoped to *only* this
   repo, **read-only**, with an expiration date (GitHub → Settings → Developer settings →
   Fine-grained tokens). Never a shared token — one per person, so it can be revoked
   individually.
2. In browser Colab (§1c) they store it in their own Colab Secrets as `GH_TOKEN`; secrets are
   per-account, so even on the same shared notebook each person's stays private to them. In
   VS Code (§1b) they use `getpass` instead.
3. The install cell is otherwise identical for everyone.

**Granting access.** For a handful of people, add them directly as Collaborators (repo →
Settings → Collaborators → Add people). They must accept the emailed invitation before they can
clone. If the team grows, or you want access managed centrally rather than repo-by-repo, move
the repo under a GitHub Organization and grant access through a Team.

**Revoking access.** Removing someone from Collaborators immediately kills their access — their
token and SSH key stop working for this repo without you having to touch the token itself.

---

## 2. Quick start

The common symbols are re-exported at the top level, so one flat import covers most of it:

```python
from great import sent_class, plat_class, MEDIA_MAP, normalize_majas
from great import sent_colors, plat_colors, emo_colors
from great import validate_export, classify_issue
from great import PROVINCE_FIX, PULAU_MAP, GEO_FIX

# Or per-module, which also works and is more explicit about where things live:
# from great.labels import sent_class, plat_class, MEDIA_MAP, normalize_majas
# from great.palette import sent_colors, plat_colors, emo_colors
```

`text` and `viz` are deliberately **not** re-exported at the top level — `great.text` lazily
imports `ftfy`/`nltk`/`Sastrawi`, and `great.viz` needs `matplotlib`/`scienceplots`. Keeping
them out means `import great` still works without those installed. Import them directly:

```python
from great.text import clean_for_bert, clean_for_topics
from great.viz import prep, checks, wordcloud
from great.viz.style import apply_style
from great.viz.overview import weekly_overview, monthly_overview
from great.viz.wordcloud import sentiment_wordclouds
```

Then the usual loading pattern:

```python

df['Sentiment'] = df['Sentiment'].str.strip().str.lower()
df['Media']     = df['Media'].replace(MEDIA_MAP)     # 'Article' -> 'News', 'Thread' -> 'Threads'
validate_export(df)                                   # raises early if something looks wrong

df['clean'] = df['Mentions'].map(clean_for_topics)     # for BERTopic / clustering
df['clean_bert'] = df['Mentions'].map(clean_for_bert)   # for IndoBERT input
```

For a worked example (sentiment-colored word cloud), see the earlier message in
this conversation, or the pattern in `great/palette.py` + `wordcloud`'s
`get_single_color_func`.

---

## 3. Module reference

| Module | What's in it | Common calls |
|---|---|---|
| `great.labels` | `sent_class`, `plat_class`, `emo_class`, `MEDIA_MAP`, majas taxonomy | `normalize_majas(text)` |
| `great.palette` | `sent_colors`, `plat_colors`, `emo_colors`, plot-size constants | — plain dicts/constants |
| `great.schema` | `EXPORT_COLUMNS`, the 13-column export shape | `validate_export(df)` |
| `great.text` | `SLANG` dict, stopword-aware cleaners | `clean_for_bert(text)`, `clean_for_topics(text, extra_stopwords=None)` |
| `great.issues` | Environmental-issue keyword rules | `classify_issue(text)` |
| `great.geo` | Province name fixes, province→island mapping | `PROVINCE_FIX`, `PULAU_MAP`, `GEO_FIX`, `ISLAND_ORDER` |
| `great.viz.prep` | Reshapes a raw export into the frames the plots consume | `prepare_data(df)`, `sentiment_data(df)`, `platform_data(df)`, `plat_sent_data(df)` |
| `great.viz.checks` | Load-time reports (they print, never raise) | `frame_info(obj, label)`, `share(series, top=None)`, `check_completeness/coverage/composition/labels(df)` |
| `great.viz.overview` | The sentiment/platform overview figure | `weekly_overview(...)`, `monthly_overview(..., interval)` |
| `great.viz.wordcloud` | Sentiment word clouds from distinctive TF-IDF terms | `sentiment_wordclouds(df)`, `prepare_corpus(df)`, `tfidf_matrix(texts)`, `distinctive_terms(X, terms, mask)`, `ramp(hex)` |
| `great.viz.style` | Shared SciencePlots figure defaults | `apply_style(dpi=500)` |

Two things worth knowing before you use them:

- **`plat_colors` keys are the canonical spelling** (`'News'`, `'Threads'`), not
  whatever a given export file calls them (`'Media Mainstream'`, `'Thread'`).
  Always run `df['Media'].replace(MEDIA_MAP)` before looking anything up in
  `plat_colors`, or you'll get a `KeyError`.
- **`clean_for_topics` and `clean_for_bert` are different on purpose.**
  `clean_for_bert` keeps case, punctuation, and stopwords (the transformer needs
  them); `clean_for_topics` lowercases, strips non-letters, and removes stopwords
  (clustering wants content words only). Don't swap them.

---

## 4. Updating the library

This section is the solo loop. If other people have push access to the repo, use the
pull-request workflow in **§9** instead of committing straight to `main`.

### You're changing `great` itself (fixing a bug, adding a function)

1. Edit the file under `great\`.
2. Because it's an **editable install**, the next `import` picks up the change —
   but Python only imports a module once per running process, so a notebook that
   already ran `from great.x import y` won't see the edit until you either restart
   the kernel, or add this once at the top of the notebook so it hot-reloads:

   ```python
   %load_ext autoreload
   %autoreload 2
   ```

3. Commit it:

   ```powershell
   cd <your clone of great>
   git add great/
   git commit -m "describe the change"
   ```

4. If this repo is pushed to GitHub already: `git push`.

### You need the latest version someone (or you, elsewhere) already pushed

- **Local:** `cd "<repo root>" && git pull` — nothing else to do; the editable install
  always reads straight from these files, there's no separate "installed copy" to
  refresh.
- **Colab:** Colab installed a snapshot via pip, so it won't see new commits on its
  own. Force it:

  ```python
  %pip install --upgrade --force-reinstall --no-deps git+https://github.com/<owner>/great.git -q
  ```

  then **Runtime → Restart runtime** — same reason as the autoreload note above:
  Python already has the old module loaded in memory.

### Pinning a stable version (once notebooks depend on this in production)

Once you don't want a future `great` change to silently break an old notebook, tag
a release:

```powershell
cd <your clone of great>
git tag v0.1.0
git push --tags
```

Then notebooks that need stability pin to it instead of `main`:

```python
%pip install git+https://github.com/<owner>/great.git@v0.1.0 -q   # pinned, reproducible
%pip install git+https://github.com/<owner>/great.git -q          # always latest, active development
```

---

## 5. Adding something new

When you find a second notebook copy-pasting the same helper, that's the signal to
move it here instead. (§9.4 lists what a reviewer checks when you do.) A few conventions worth keeping:

- Small, pure functions and constants — no `st.something`, no `input()`, nothing
  that only makes sense inside one specific notebook's flow.
- A one-line docstring is fine; only write more if there's a **non-obvious reason**
  behind the code (see `issues.py`'s docstring for an example — it explains *why*
  the classifier scores every rule instead of taking the first match).
- If it needs a new third-party package, add it to `pyproject.toml` — to
  `dependencies` if every user of `great` needs it (like `pandas`), or to
  `[project.optional-dependencies] text = [...]` style if only one function needs
  it (like `text.py`'s lazy `import nltk`).
- After adding, re-run the pattern from §4 (edit → autoreload or restart → commit).

---

## 6. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'great'` | Installed into a different Python than your notebook kernel uses | Check `sys.executable` in the notebook; reinstall with that exact interpreter |
| `ImportError: clean_for_bert() requires ftfy` | Optional text extras not installed | `pip install ftfy` or reinstall with `[text]` |
| `ImportError: clean_for_topics() requires nltk and PySastrawi` | Same as above | `pip install nltk PySastrawi` or reinstall with `[text]` |
| `KeyError` on `plat_colors[...]` | Looked up a raw export spelling (`'Media Mainstream'`) instead of canonical (`'News'`) | `df['Media'].replace(MEDIA_MAP)` first |
| Edited `great` but the notebook still behaves like the old version | Python already imported the old module in this kernel | Restart the kernel, or use `%autoreload 2` (see §4) |
| Colab still runs the old `great` after you pushed a fix | pip installed a snapshot, doesn't auto-update | `--force-reinstall` + **Restart runtime** (see §4) |
| `nltk.download(...)` hangs or fails inside `clean_for_topics` | No internet in that environment, or first-run download blocked | Run `import nltk; nltk.download('stopwords')` once manually in that environment first |
| Dates in the archived `pol_weekly_viz.ipynb` / `pol_monthly_viz.ipynb` come out with day and month swapped | Those notebooks still carry the original `pd.to_datetime(..., format='mixed', dayfirst=True)`. pandas 3 applies `dayfirst` to ISO input too; the exports store Date as ISO (`2026-07-03 16:58:03`), so any day &le; 12 gets flipped | Don't re-run them for numbers &mdash; they are kept as the historical record. Use `great.viz.prep.prepare_data()` (or the `example_*_with_great.ipynb` notebooks), which parses with `format='ISO8601'`. See the note below |

---

### The `dayfirst` date bug in the archived notebooks

`pol_weekly_viz.ipynb` and `pol_monthly_viz.ipynb` parse dates with:

```python
pd.to_datetime(data['Date'], format='mixed', dayfirst=True)
```

On the pandas the notebooks were originally run against, `dayfirst` was ignored for
ISO-8601 input. **pandas 3 honours it**, so the same line now reads an ISO string
day-first and swaps the two fields:

```python
pd.to_datetime(pd.Series(['2026-07-01 10:00:00']), format='mixed', dayfirst=True)
# -> 07 Jan 2026   (wrong)
pd.to_datetime(pd.Series(['2026-07-01 10:00:00']), format='ISO8601')
# -> 01 Jul 2026   (correct)
```

Two things make this easy to miss:

- **It is selective.** A day past the 12th can't be read as a month, so it survives
  untouched. One file ends up with a mix of correct and swapped dates rather than an
  obvious across-the-board shift, and a file covering only the back half of a month
  (e.g. `prabowo_agustus1.xlsx`, 16-31 Aug) is not visibly affected at all.
- **Nothing raises.** The wrong dates flow straight into the period labels in every plot
  title, `monthly_overview`'s trend x-axis, `check_coverage()`'s day counts and
  peak/quietest day, and the `sort_values('Date')` ordering.

The stored outputs inside the archived notebooks are from the original run and are
correct &mdash; `pol_weekly_viz.ipynb` shows `01 Jul 2026 - 03 Jul 2026` for
`prabowo_juli3.xlsx`. Re-running that same cell today yields `07 Jan 2026 - 07 Mar 2026`.
The archived notebooks are deliberately left unedited, so this will keep happening;
treat their saved outputs as the record and use `great` for anything new.

`great.viz.prep.prepare_data()` parses with `format='ISO8601'`, which is both correct for
these exports and loud &mdash; it raises if an export ever arrives in a different layout
instead of silently mis-parsing it.

---

## 7. Uninstall

```powershell
py -3.11 -m pip uninstall great
```

Safe — it only removes the link created by `pip install -e`, never touches the
files in `great\`.

---

## 8. Worked examples

Two notebooks in this repo exist purely to demonstrate the library end to end:

| Notebook | Shows |
|---|---|
| `Weekly Visualization/example_weekly_with_great.ipynb` | The full flow with every argument passed explicitly |
| `Monthly Visualization/example_monthly_with_great.ipynb` | The same flow leaning on the library defaults, plus the trend panel's `interval` |

Both run top to bottom unattended against the export files, which live outside this repo
(see the `DATA` cell near the top of each notebook, and `.gitignore` — exports are never
committed). Point that cell at wherever you keep them; on a cloud runtime see §1b.

The originals they were derived from — `pol_weekly_viz.ipynb` and `pol_monthly_viz.ipynb` —
are left exactly as they were, as the archived record of how the analysis was first written.
They still carry their own copy-pasted helpers and do not import `great`.
---

## 9. Collaborating on the library

§4 covers changing the library when you are the only one touching it. This section is the
multi-person version: how a teammate gets started, how changes get in, and the handful of
mistakes that are specific to *this* package.

The whole point is that a helper written once ends up in `great/` where everyone gets it,
instead of being pasted into a fourth notebook. Everything below serves that.

### 9.1 Day one for a new collaborator

1. Accept the emailed repository invitation (you cannot clone before this).
2. Clone and install — see §1a for the full explanation:
   ```bash
   git clone https://github.com/<owner>/great.git
   cd great
   py -3.11 -m pip install -e ".[all]"
   ```
3. Set your identity, so reviewers know whose commit is whose:
   ```bash
   git config user.name "Your Name"
   git config user.email "you@example.com"
   ```
4. Prove it worked, **from a directory that is not the clone**:
   ```bash
   py -3.11 -c "from great import sent_colors; from great.viz import weekly_overview; print(sent_colors)"
   ```
   Printing the palette means `great` is importable from any notebook on your machine. If it
   fails, you are in §1a's `ModuleNotFoundError` case — wrong interpreter.
5. Read §2 (quick start), §3 (module reference) and §5 (what belongs in the library).

### 9.2 The change loop

Never commit to `main` directly. One branch per change, reviewed by someone else, merged
through a pull request. That single rule is what keeps this library from rotting back into
copy-paste.

```bash
git pull                              # always start from current main
git checkout -b fix-date-parsing      # one branch, one concern
#   ...edit, test (§9.5)...
git add -A
git commit -m "Parse dates as ISO8601 so pandas 3 stops swapping day and month"
git push -u origin fix-date-parsing
```

Then open a Pull Request on GitHub, get a review, merge it, and delete the branch. Afterwards
everyone else picks it up with a plain `git pull` — no reinstall, because §1a installed it
editable.

**Branch names** — a prefix and a few words: `fix-`, `add-`, `docs-`, `refactor-`.
E.g. `add-emotion-palette`, `docs-colab-setup`.

**Commit messages** — say *why*, not *what*; the diff already shows what. "Parse dates as
ISO8601 so pandas 3 stops swapping day and month" tells the next person something.
"Update prep.py" does not.

**Keep your branch current.** If `main` moved while you were working:

```bash
git pull --rebase origin main
```

Rebase keeps history linear and readable. One caveat: do not rebase a branch someone else has
already pulled — it rewrites commits they have, and their next pull will conflict messily. If
someone else is on your branch, use `git merge origin/main` instead.

### 9.3 Protecting `main`

Worth two minutes: repo → **Settings → Branches → Add branch protection rule** → branch name
`main` → tick **Require a pull request before merging**. This turns "nobody commits to main
directly" from a convention people forget into something GitHub enforces.

### 9.4 Reviewing a pull request

Beyond the usual "does it work", these four are the failure modes this package has actually
hit. They are worth checking every time.

**1. Does the code read a name it never received?** In a notebook everything is global, so a
function can read a variable it was never passed and still work. Moved into a module, the same
function raises `NameError`. Three functions here did exactly that — `plot_sentiment_platform_overview`
read `ps_data`, `plat_data` and `sent_data` off the notebook's globals. Every input a function
uses must be a parameter.

**2. Is a new dependency in the right extra?** `pyproject.toml` splits deps into `text`, `ml`,
`viz` and `all`. Anything imported **at module level** under `great/viz/` must be reachable
from the `viz` extra, or `from great.viz import prep` breaks for everyone — this happened when
`scikit-learn` was moved into its own `ml` extra while `great/viz/wordcloud.py` still imported
`TfidfVectorizer` at import time. `viz` now includes `great[ml]` for that reason. Also confirm
`import great` alone still does not require matplotlib, sklearn or wordcloud.

**3. Does it belong in the library?** §5's rule: move it in when a *second* notebook needs it.
One-off analysis stays in the notebook.

**4. Does it change results for existing notebooks?** If a function's output changes, say so
in the PR — see §9.6.

### 9.5 Testing before you push

There is no test suite, so these are the checks. Run them from the repo root unless noted.

```bash
# 1. Everything still imports, from OUTSIDE the clone
cd /
py -3.11 -c "import great; from great.viz import prep, checks, wordcloud, weekly_overview, monthly_overview; print('ok')"

# 2. The core stays lightweight - this must print False False False
py -3.11 -c "import sys, great; print('matplotlib' in sys.modules, 'sklearn' in sys.modules, 'wordcloud' in sys.modules)"
```

Then re-run both example notebooks end to end and confirm zero errors — they are the closest
thing to an integration test:

```bash
py -3.11 -c "import nbformat; from nbclient import NotebookClient; [NotebookClient(nbformat.read(p, as_version=4), timeout=1800, kernel_name='python3').execute() for p in [r'Weekly Visualization\example_weekly_with_great.ipynb', r'Monthly Visualization\example_monthly_with_great.ipynb']]; print('both notebooks ran clean')"
```

If you changed anything that feeds a number, compare the returned `sent_pct_df` and
`platform_totals_df` against the previous run before and after. A refactor that is meant to
change nothing should change nothing.

### 9.6 Breaking changes and versions

Everyone's notebooks import the same package, so renaming or removing a function breaks their
work silently at their next `git pull`. When that is unavoidable:

1. Say so plainly in the PR description, including what to rename.
2. Bump `version` in `pyproject.toml`.
3. Tag the release so old notebooks can pin a known-good version:
   ```bash
   git tag v0.2.0
   git push --tags
   ```

§4 documents the pinned-install syntax for Colab. Prefer adding a new function over changing
an existing one's behaviour; deprecate rather than delete when you can.

### 9.7 Notebook conflicts — read this before editing a notebook

The notebooks in this repo keep their outputs, including embedded figures. That makes them
megabytes of base64, and **git cannot merge two people's edits to the same notebook.** You
will get a conflict that is impossible to resolve by hand.

The rules that avoid it:

- **One person owns a notebook at a time.** Say in the PR (or just tell the team) that you are
  editing it before you start.
- **Never hand-merge notebook JSON.** If you do hit a conflict, take one side whole and re-run:
  ```bash
  git checkout --theirs "Monthly Visualization/example_monthly_with_great.ipynb"
  # or --ours to keep your version
  ```
  then re-execute the notebook top to bottom and commit the result.
- **Prefer changing the library over the notebook.** Python files in `great/` merge cleanly
  like any code. A notebook does not. This is the same instinct §5 asks for, with a second
  reason behind it.

If notebook conflicts become routine, revisit stripping outputs from the two `example_*`
notebooks — they regenerate in about two minutes. The two archived `pol_*_viz.ipynb` should
keep their outputs regardless: the `dayfirst` bug in §6 means re-running them now produces
*wrong dates*, so their stored outputs are the only correct record of that analysis.

### 9.8 What never gets committed

- **Data exports.** `.gitignore` blocks `*.xlsx`, `*.xls`, `*.csv` and `*.zip`. Keep it that
  way — the exports contain real mention text and author names, and they are large.
- **Tokens, of any kind.** Not in a cell, not in a file, not in a commit message. §1b and §1d
  cover doing it properly. If one leaks, revoke it on GitHub immediately; deleting the commit
  is not enough, because it stays in the history and in every clone.
- **Virtualenvs** (`.venv/`) and build artifacts — also gitignored.

A private repo is not a safe place for secrets. Every collaborator can read everything in it,
and access can outlive your intent.
