# Build a Bloom Filter

My working repo for [Build a Bloom Filter](https://shipthatcode.com/courses/build-bloom-filter) on [shipthatcode.com](https://shipthatcode.com) — built lesson by lesson in my own editor.

## What you need

- **git** and a terminal (macOS/Linux: the built-in one; Windows: see below)
- Python 3 (`python3 --version` should work)
- any editor you like — VS Code, Vim, JetBrains, anything

### On Windows

Use **WSL** if you can: run `wsl --install` in an admin PowerShell once, then do everything (git, editing, `./run_tests.sh`) inside the Ubuntu terminal — it behaves exactly like the grader.

[Git Bash](https://git-scm.com/downloads) (installs with git) also runs `./run_tests.sh`. One caveat: native Windows compilers and runtimes write Windows line endings (`\r\n`), so on byte-exact tests you can see local FAILs where the diff looks identical — your logic is fine, the invisible line endings differ. If that happens, trust **Check my solution** on the lesson page (graded on Linux), or switch to WSL.

## Getting started (one-time setup)

1. Unzip this download and open the folder in your editor.
2. Create a new **empty, public** repo at [github.com/new](https://github.com/new) — leave "Add a README" and ".gitignore" **unchecked** (this folder already has both).
3. In your terminal, inside the unzipped folder, push it to GitHub:

   ```sh
   git init
   git add .
   git commit -m "start Build a Bloom Filter"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
   git push -u origin main
   ```

4. Paste your repo link on the [course page](https://shipthatcode.com/courses/build-bloom-filter) ("Work in your own editor" → **Link repo**). Done — you never do this again.

## The lesson loop

1. Read the lesson on shipthatcode, write your code in `main.py` here.
2. Test locally against **the lesson you're on**: `./run_tests.sh 01`, `./run_tests.sh 02`, and so on. On Windows, run this inside Git Bash. (A bare `./run_tests.sh` runs every lesson's tests, which is only useful on courses where one program answers all of them — see below.)
3. When it passes: `git add -A && git commit -m "lesson 01" && git push`
4. Hit **Check my solution** on the lesson page — shipthatcode pulls this repo and grades it against the full suite, including hidden tests.

## How this repo is laid out

- `main.py` — the program you're grading right now.
- `tests/` — the public test cases per lesson (`tests/01-…/1.in` → expected `1.out`).
- `run_tests.sh` — the local runner. `.shipthatcode.json` tells the grader what this repo is; don't delete either.

### One lesson at a time

Each lesson states its own input and output format, and **most lessons are a separate exercise rather than a bigger version of the last one**. Two lessons can be handed the same input line and correctly want different output — a tokenizer prints `[ls] [-la]`, while the next lesson, which receives already-tokenized input, prints `ls -la`. No single program can satisfy both, and it isn't supposed to.

So treat `main.py` as the file for the lesson you're grading: when you move on, change what it does. Nothing is lost — every earlier lesson is in your git history (`git log`, `git show`), and shipthatcode remembers each lesson you passed, so a lesson stays completed even after you replace the code that passed it. If you'd rather keep the code visible, copy it aside first (`cp main.py solutions/01-<lesson>.py`) — extra files are ignored by the grader.

When a lesson genuinely does build on the previous one, its own text says so and its tests will pass with the earlier behaviour still in place.

## Reusing this project in another application

Anyone can clone this repository and run it with Python 3; it has no third-party dependencies. The current `main.py` is a command-line learning exercise, not an installable library, plugin, or Java `.jar`. It cannot be injected into a JVM as-is. A Java application (or another language) can launch Python as a separate process, but that is process integration, not jar injection.

The program reads a complete command sequence from standard input and prints its replies after input ends. For example, from this repository:

```sh
python3 main.py <<'EOF'
INIT 100 0.01
PUT_CACHE user:42 Alice Smith
GET user:42
INVALIDATE user:42
GET user:42
REBUILD
GET user:42
STATS
EOF
```

An application can send the same batch through a subprocess. In Python:

```python
import subprocess
import sys

commands = """\
INIT 100 0.01
PUT_CACHE user:42 Alice Smith
GET user:42
STATS
"""
result = subprocess.run(
    [sys.executable, "main.py"],
    input=commands,
    text=True,
    capture_output=True,
    check=True,
)
print(result.stdout)
```

Java can use `ProcessBuilder` to launch `python3 main.py`, write commands to the process's standard input, close the input stream, and read the replies from standard output. This command-line interface is batch-oriented: its cache and filter live only for that run. For a long-lived service or direct imports, extract the filter/cache logic into an importable Python module or expose it through a service API. To use it as a Java library, it would need a Java implementation packaged as a `.jar`.
[![shipthatcode — Build a Bloom Filter](https://api.shipthatcode.com/cert/e717bcaf13f52efe1b94c409bfcef9fb.svg)](https://shipthatcode.com/courses/build-bloom-filter)

## If the course gets updated

Courses improve over time — exercises get added, tests get fixed. If the [course page](https://shipthatcode.com/courses/build-bloom-filter) says your starter is out of date: download a fresh zip, **delete this repo's `tests/` folder entirely**, copy in the fresh `tests/` and `.shipthatcode.json`, and keep your own code exactly as it is. (Don't merge test folders — lesson numbering can shift between versions.) Lessons you've already completed stay completed either way.

<sub>Repo topic suggestion: `shipthatcode` · Starter generated by [shipthatcode.com](https://shipthatcode.com)</sub>
