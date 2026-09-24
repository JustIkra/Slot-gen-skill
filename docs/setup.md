# Install and run

From this repository, create a project-local Python environment and install the package:

    python3 -m venv .venv
    .venv/bin/python -m pip install -e '.[art]'

Use that interpreter for local processing scripts. Old Spine command paths
additionally need the sibling package installed with pip install -e ../slot-spine-skin.

The BB `qwen-review` provider reads OPENROUTER_KEY on its host. Keep its value
out of chat, commands and reports.

Offline smoke test (no key or spend):

    PYTHON="$PWD/.venv/bin/python" .venv/bin/python -m unittest discover -s tests

New generation jobs await a BB generation agent and model choice. Keep existing
outputs and job records in the target game's ignored .tmp_<task>/, not in the
skill source tree or system /tmp. Native Codex image requests use the imagegen
tool when explicitly requested.

The shared MorningCat installation uses .local/skills-venv; it is convenience configuration,
not a prerequisite on another machine. Exact tested dependency versions are recorded in
requirements.lock. A fresh installation can use pip -c requirements.lock.
