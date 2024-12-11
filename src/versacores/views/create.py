from .base import ViewBase
from versacores.core import Core
from versacores.exceptions import CoreFileError

class CreateView(ViewBase):
    def depend_on(self, **kwargs):
        name = kwargs.pop("name", None)
        version = kwargs.pop("version", None)
        repo = kwargs.pop("repo", None)
        if not name:
            raise CoreFileError("Name of dependency not specified")
        core = Core.from_name(name)
        core.create(**kwargs)
        self._core.dependencies.append(core)

    def depend_on_foreign(self, name: str, type: str, **kwargs):
        pass

    def is_singleton(self, value: bool):
        pass

    def set_vlog_defines(self, **kwargs):
        pass

