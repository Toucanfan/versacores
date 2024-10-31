# Flow:
# 1. Find toplevel core (if only a single versacore in ./ use that - otherwise use top name configured in versaconf (by default top.versacore))
# 2. Recursively build core dependency graph
# 3. Run various sanity checks on the graph, e.g. check that it is acyclical
# 
# 
# Config application order: ./versacores.conf, $VERSACORES_CONF, $GIT_ROOT/versacores.conf, ~/.config/versacores.conf, /etc/versacores.conf
# Core search order: ./, $VERSACORES_PATH, ($GIT_ROOT/cores | as configured in project versaconf), as otherwise configured in versaconf(applied hierarchially as described above)
# 
# 
# The cli tool: versacores
# By default operates on project level config (like git). However, can be overridden with either --user or --global switch (similar to git)
# Can be used to do configuration, repo management, etc.
# 
import asyncio
import importlib
from pathlib import Path
import traceback
import logging
import sys

from .exceptions import FatalError, CoreFileError
from .versacore import VersaCore

logger = logging.getLogger(__name__)


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


def main():
    try:
        top = VersaCore(get_top_core_path())
        top.top()
        asyncio.run(top.generate())
        return 0
    except CoreFileError as e:
        tb_list = traceback.extract_tb(e.__traceback__)
        logger.error("Error in core file:\n")
        logger.error(''.join(traceback.format_list(tb_list[-2:-1])))
        logger.error(e)
        return 1
    except Exception as e:
        logger.error(traceback.format_exc())
        logger.error(e)
        return 1

if __name__ == "__main__":
    sys.exit(main())
