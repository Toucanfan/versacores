import asyncio
import importlib
import importlib.util
import itertools
from pathlib import Path
import traceback
import logging
from typing import Callable, Iterable, List

from simplhdl.pyedaa.fileset import FileSet

from .views import TopView, CreateView, GenerateView
from .exceptions import FatalError, CoreFileError
from .utils import import_module_from_path, find_corefile

logger = logging.getLogger(__name__)

class Target:
    def __init__(self, name: str):
        self.name = name
        self.core_parameters = {}

    def set_core_parameters(self, **kwargs):
        self.core_parameters.update(kwargs)

class Core:
    path: Path
    targets: List[Target]
    default_target: Target
    dependencies: List['Core']
    fileset: FileSet

    @classmethod
    def from_path(cls, path: Path) -> 'Core':
        if not path.is_file():
            raise CoreFileError(f"The core file '{path}' does not exist")
        core = cls(path)
        return core

    @classmethod
    def from_name(cls, name: str, **filters) -> 'Core':
        locations = filters.pop("locations", [Path.cwd()])
        path = find_corefile(name, locations)
        if not path:
            raise CoreFileError(f"The core '{name}' cannot be found")
        return cls.from_path(path)

    def __init__(self, path: Path):
        self.path = path.absolute()
        self.targets = []
        self.default_target = None
        self.dependencies = []
        self.fileset = FileSet(self.path.name)

        self.load_corefile(path)

    def _assert_corefile_has_attr(self, attr: str, type: type = None, optional: bool = False):
        has_attr = hasattr(self.corefile, attr)
        if not has_attr and not optional:
            raise CoreFileError(f"The corefile '{self.path}' does not have the required attribute '{attr}'")
        if has_attr and type and not isinstance(getattr(self.corefile, attr), type):
            raise CoreFileError(f"The corefile '{self.path}' attribute '{attr}' is not of type {type.__name__}")

    def load_corefile(self, path: Path):
        self.corefile = import_module_from_path(path)
        # Check that the corefile is valid
        self._assert_corefile_has_attr("NAME", str)
        self._assert_corefile_has_attr("VERSION", str)
        self._assert_corefile_has_attr("API_VERSION", str)
        self._assert_corefile_has_attr("DESCRIPTION", str)
        self._assert_corefile_has_attr("TOP", Callable, optional=True)
        self._assert_corefile_has_attr("CREATE", Callable)
        self._assert_corefile_has_attr("GENERATE", Callable)
        self._assert_corefile_has_attr("CLEAN", Callable, optional=True)
        self._assert_corefile_has_attr("GET_SOURCES", Callable, optional=True)
        self._assert_corefile_has_attr("PREPARE_SOURCES", Callable, optional=True)

    def top(self):
        self.corefile.TOP(TopView(self))
        if not self.default_target:
            raise FatalError(f"The top level core ('{self.path}') does not define a default target.")
        self.create(**self.default_target.core_parameters)

    def create(self, **kwargs):
        self.corefile.CREATE(CreateView(self), **kwargs)

    async def generate(self):
        to_run = [dep.generate() for dep in self.dependencies]
        await asyncio.gather(*to_run)
        await self.corefile.GENERATE(GenerateView(self))
