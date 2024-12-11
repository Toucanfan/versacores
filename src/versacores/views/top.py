from .base import ViewBase
from versacores.core import Target
from versacores.exceptions import CoreFileError
from versacores.utils import find_first_where

class TopView(ViewBase):
    def define_target(self, name: str) -> Target:
        """ Creates a new target for the core.
        A target determines the flow, toolchain, and options for the core
        when it is used as the project top. If multiple targets are defined for the same core,
        the user can choose among them on the command line, otherwise the default target is used.

        Args:
            name: The name of the target.

        Returns:
            The target object.
        """

        target = Target(name)
        self._core.targets.append(target)
        return target

    def set_default_target(self, name: str):
        """ Sets the default target for the core.
        The default target is used when no specific target is chosen on the command line.

        Args:
            name: The name of the target to set as default.
        """

        target = find_first_where(self._core.targets, name=name)
        if not target:
            raise CoreFileError(f"Target '{name}' does not exist")
        self._core.default_target = target