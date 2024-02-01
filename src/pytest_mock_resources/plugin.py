import importlib
import sys
from typing import Iterable

if sys.version_info < (3, 8):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata


def find_entrypoints() -> Iterable[str]:
    modules = set()
    for dist in importlib_metadata.distributions():
        for ep in dist.entry_points:
            if ep.group.lower() != "pmr":
                continue

            modules.add(ep.value)
    return sorted(modules)


def load_entrypoints(modules: Iterable[str]):
    for module in modules:
        importlib.import_module(module)
