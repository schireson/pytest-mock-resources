from __future__ import annotations

import abc
from typing import ClassVar, Iterable


class AbstractAction(metaclass=abc.ABCMeta):
    fixtures: ClassVar[tuple[str, ...]] = ()
    static_safe: ClassVar[bool] = False

    @abc.abstractmethod
    def apply(self, conn):
        """Execute an action against the provided fixture connection."""


def validate_actions(actions, *, fixture: str | None, additional_types: Iterable = ()):
    for action in actions:
        if not isinstance(action, (AbstractAction, *additional_types)):
            extra_types_str = ", ".join(
                ["`" + ".".join([cls.__module__, cls.__name__]) + "`" for cls in additional_types]
            )
            raise ValueError(
                f"`{action}` invalid: create_{fixture}_fixture function accepts "
                f"{extra_types_str}, or `AbstractAction` subclasses as inputs."
            )

        if fixture and isinstance(action, AbstractAction) and fixture not in action.fixtures:
            supported_fixtures = ", ".join([f"`create_{f}_fixture`" for f in action.fixtures])
            raise ValueError(
                f"`{action}` invalid: `{action.__class__}` is being used with `create_{fixture}_fixture` "
                f"but only supports: {supported_fixtures}."
            )
