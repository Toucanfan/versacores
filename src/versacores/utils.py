from typing import Iterable
from pathlib import Path
import importlib.util

from .exceptions import FatalError

def find_first_where(objs, **kwargs):
    for obj in objs:
        matching = True
        for k, v in kwargs.items():
            if not getattr(obj, k) == v:
                matching = False
                break
        if matching:
            return obj
    return None

def get_top_core_path(cwd=Path.cwd()) -> Path:
    cores = list(cwd.glob("*.versacore"))
    if not cores:
        raise FatalError("No cores found in current directory.")
    elif len(cores) == 1:
        return cores[0]
    elif cwd.joinpath("top.versacore").is_file():
        return cwd.joinpath("top.versacore")
    else:
        raise FatalError("Multiple cores found in current directory.")

def import_module_from_path(file_path: Path):
    # Load the module spec from the given file path
    if file_path.name.count('.') > 2:
        raise FatalError(f"Core file {file_path.name} cannot have '.' in its name")
    name = file_path.name.split('.')[0]
    spec = importlib.util.spec_from_loader(name, importlib.machinery.SourceFileLoader(name, str(file_path)))
    if spec is None:
        raise ImportError(f"Could not load module '{name}' from '{file_path}'")
    # Create a new module based on the spec
    module = importlib.util.module_from_spec(spec)
    # Execute the module to initialize it
    spec.loader.exec_module(module)
    return module

def find_corefile(name, locations: Iterable[Path]) -> Path:
    for loc in locations:
        corefile = loc.joinpath(f"{name}.versacore")
        if corefile.is_file():
            break
        corefile = None
    return corefile