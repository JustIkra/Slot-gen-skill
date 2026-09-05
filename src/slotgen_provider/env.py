import os
from pathlib import Path


def provider_key(name):
    if os.environ.get(name):
        return os.environ[name]
    file = Path.home() / '.codex/.env'
    if file.is_file():
        for raw in file.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            if key.strip() == name:
                value = value.strip().strip('"').strip("'")
                if value:
                    return value
    raise ValueError(f'Missing provider credential: {name}')
