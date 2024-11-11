from typing import Optional
from pathlib import Path
from argparse import Namespace
import logging
from simplhdl.parser import ParserBase, ParserFactory
from simplhdl.pyedaa.project import Project
from simplhdl.pyedaa.fileset import FileSet

logger = logging.getLogger(__name__)

@ParserFactory.register()
class VersaCoreParser(ParserBase):
    def __init__(self):
        super().__init__()
        logger.debug("VersaCoreParser initialized")
        

    def is_valid_format(self, filename: Optional[Path]) -> bool:
        if not filename:
            return (Path.cwd() / "top.versacore").is_file()
        return filename.suffix == ".versacore"

    def parse(self, filename: Optional[Path], project: Project, args: Namespace) -> FileSet:
        return FileSet('Empty')
