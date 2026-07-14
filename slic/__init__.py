import tomllib
from pathlib import Path

with open(Path(__file__).parent.parent / 'pyproject.toml', 'rb') as f:
    __version__ = tomllib.load(f)['project']['version']
