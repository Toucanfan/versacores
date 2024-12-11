import asyncio
import itertools
import logging

from simplhdl.pyedaa import (
    IPSpecificationFile, TCLSourceFile, CocotbPythonFile, SettingFile, File,
    ConstraintFile, VHDLSourceFile, VerilogIncludeFile, SystemVerilogSourceFile,
    EDIFNetlistFile, NetlistFile, CSourceFile, SourceFile, ChiselBuildFile)

from .base import ViewBase
from versacores.core import Core
from versacores.exceptions import CoreFileError

logger = logging.getLogger(__name__)

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