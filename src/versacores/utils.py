from pathlib import Path
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