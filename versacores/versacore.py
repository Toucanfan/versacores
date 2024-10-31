import asyncio
import importlib
import importlib.util
import itertools
from pathlib import Path
import traceback
import logging
from typing import Callable, Iterable, List

from simplhdl.pyedaa import (
    IPSpecificationFile, TCLSourceFile, CocotbPythonFile, SettingFile, File,
    ConstraintFile, VHDLSourceFile, VerilogIncludeFile, SystemVerilogSourceFile,
    EDIFNetlistFile, NetlistFile, CSourceFile, SourceFile, ChiselBuildFile)
from simplhdl.pyedaa.fileset import FileSet

from .exceptions import FatalError, CoreFileError
from .utils import find_first_where

logger = logging.getLogger(__name__)

def _import_module_from_path(file_path: Path):
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

class Target:
    def __init__(self, name: str):
        self.name = name
        self.core_parameters = {}

    def set_core_parameters(self, **kwargs):
        self.core_parameters.update(kwargs)

class VersaCoreViewBase:
    def __init__(self, versacore):
        self._versacore = versacore

    @staticmethod
    def say_hello(msg):
        print(msg)

class VersaCoreTopView(VersaCoreViewBase):
    def define_target(self, name: str) -> Target:
        target = Target(name)
        self._versacore.targets.append(target)
        return target

    def set_default_target(self, name: str):
        target = find_first_where(self._versacore.targets, name=name)
        if not target:
            raise CoreFileError(f"Target '{name}' does not exist")
        self._versacore.default_target = target

class VersaCoreCreateView(VersaCoreViewBase):
    def depend_on(self, **kwargs):
        name = kwargs.pop("name", None)
        ver = kwargs.pop("ver", None)
        repo = kwargs.pop("repo", None)
        if not name:
            raise CoreFileError("Name of dependency not specified")
        corefile = find_corefile(name, locations=[Path.cwd()])
        if not corefile:
            raise CoreFileError(f"The core '{name}' cannot be found")
        core = VersaCore(corefile)
        core.create(**kwargs)
        self._versacore.dependencies.append(core)

    def depend_on_foreign(self, name: str, type: str, **kwargs):
        pass

    def is_singleton(self, value: bool):
        pass

    def set_vlog_defines(self, **kwargs):
        pass


class VersaCoreGenerateView(VersaCoreViewBase):
    fileClasses = {
        '.sv': SystemVerilogSourceFile,
        '.svh': VerilogIncludeFile,
        '.v': SystemVerilogSourceFile,
        '.vh': VerilogIncludeFile,
        '.vhd': VHDLSourceFile,
        '.vhdl': VHDLSourceFile,
        '.xdc': ConstraintFile,
        '.sdc': ConstraintFile,
        '.xci': IPSpecificationFile,
        '.xcix': IPSpecificationFile,
        '.ip': IPSpecificationFile,
        '.ipx': IPSpecificationFile,
        '.qip': IPSpecificationFile,
        '.qsys': IPSpecificationFile,
        '.edif': EDIFNetlistFile,
        '.edn': EDIFNetlistFile,
        '.dcp': NetlistFile,
        '.tcl': TCLSourceFile,
        '.c': CSourceFile,
        '.h': CSourceFile,
        '.S': CSourceFile,
        '.py': CocotbPythonFile,
        '.qsf': SettingFile,
        '.sbt': ChiselBuildFile,
    }

    async def run_cmd(self, cmd: str):
        process = await asyncio.create_subprocess_exec(
            *cmd.split(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self._versacore.path.parent
        )
        stdout, stderr = await process.communicate()
        if stdout:
            logger.info(f"{self._versacore.path.name}: {stdout.decode()}")
        if stderr:
            logger.error(f"{self._versacore.path.name}: {stderr.decode()}")
        if process.returncode != 0:
            raise CoreFileError(f"Command '{cmd}' failed with return code {process.returncode}")

    def add_files(self, *files: str, **kwargs):
        filetype = kwargs.pop("type", None)
        useIn = kwargs.pop("useIn", None)
        coredir = self._versacore.path.parent
        for file in itertools.chain.from_iterable(coredir.glob(glob) for glob in files):
            if not file.is_file():
                raise CoreFileError(f"File '{file}' does not exist")
            fileClass = self.fileClasses.get(file.suffix, SourceFile)
            self._versacore.fileset.AddFile(fileClass(file))

    def set_top(self, file: str):
        self._versacore.fileset.SetTop(file)

    @property
    def dependencies(self):
        return self._versacore.dependencies


class VersaCore:
    path: Path
    targets: List[Target]
    default_target: Target
    dependencies: List['VersaCore']
    fileset: FileSet

    def __init__(self, path: Path):
        self.path = path
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
        self.corefile = _import_module_from_path(path)
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
        self.corefile.TOP(VersaCoreTopView(self))
        if not self.default_target:
            raise FatalError(f"The top level core ('{self.path}') does not define a default target.")
        self.create(**self.default_target.core_parameters)

    def create(self, **kwargs):
        self.corefile.CREATE(VersaCoreCreateView(self), **kwargs)

    async def generate(self):
        to_run = [dep.generate() for dep in self.dependencies]
        await asyncio.gather(*to_run)
        await self.corefile.GENERATE(VersaCoreGenerateView(self))
