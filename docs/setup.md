# Install and run

From this repository, create a project-local Python environment and install the package:

    python3 -m venv .venv
    .venv/bin/python -m pip install -e '.[art]'

Use that interpreter for scripts. For the Bun compatibility frontend set PYTHON to the
same interpreter; Bun itself must be installed. Old Spine command paths additionally need
the sibling package installed with pip install -e ../slot-spine-skin.

Credentials are read by name from the environment or ~/.codex/.env; create/edit that private
file outside chat/tool arguments. Do not print values or put them into command examples.
Image/video/vision use OPENROUTER_KEY. No direct Google credential is needed for this route.

Offline smoke test (no key or spend):

    .venv/bin/python scripts/openrouter_image.py generate --prompt fixture --dry-run
    .venv/bin/python -m unittest discover -s tests

Run paid generation only for a requested asset task and agreed scope. Keep outputs and job
records in the target game's ignored .tmp_<task>/, not in the skill source tree or system /tmp.
Native Codex image requests use the imagegen tool instead of changing OpenRouter aliases.

The shared MorningCat installation uses .local/skills-venv; it is convenience configuration,
not a prerequisite on another machine. Exact tested dependency versions are recorded in
requirements.lock. A fresh installation can use pip -c requirements.lock.
