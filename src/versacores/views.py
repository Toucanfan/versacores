from pathlib import Path
import asyncio
import itertools
import logging

from simplhdl.pyedaa import (
    IPSpecificationFile, TCLSourceFile, CocotbPythonFile, SettingFile, File,
    ConstraintFile, VHDLSourceFile, VerilogIncludeFile, SystemVerilogSourceFile,
    EDIFNetlistFile, NetlistFile, CSourceFile, SourceFile, ChiselBuildFile)

from .utils import find_first_where, find_corefile
from .core import Target, Core
from .exceptions import CoreFileError

logger = logging.getLogger(__name__)

class ViewBase:
    def __init__(self, core):
        self._core = core

    @staticmethod
    def say_hello(msg):
        print(msg)

class TopView(ViewBase):
    def define_target(self, name: str) -> Target:
        target = Target(name)
        self._core.targets.append(target)
        return target

    def set_default_target(self, name: str):
        target = find_first_where(self._core.targets, name=name)
        if not target:
            raise CoreFileError(f"Target '{name}' does not exist")
        self._core.default_target = target

class CreateView(ViewBase):
    def depend_on(self, **kwargs):
        name = kwargs.pop("name", None)
        version = kwargs.pop("version", None)
        repo = kwargs.pop("repo", None)
        if not name:
            raise CoreFileError("Name of dependency not specified")
        corefile = find_corefile(name, locations=[Path.cwd()])
        if not corefile:
            raise CoreFileError(f"The core '{name}' cannot be found")
        core = Core(corefile)
        core.create(**kwargs)
        self._core.dependencies.append(core)

    def depend_on_foreign(self, name: str, type: str, **kwargs):
        pass

    def is_singleton(self, value: bool):
        pass

    def set_vlog_defines(self, **kwargs):
        pass


class GenerateView(ViewBase):
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