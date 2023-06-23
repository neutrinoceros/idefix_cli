import sys
from enum import auto

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from idefix_cli._backports import StrEnum


class Theme(StrEnum):
    DEFAULT = auto()
    BABALLE = auto()


THEME = Theme("default")


def set_theme(theme: str) -> None:
    global THEME
    THEME = Theme(theme)


def get_theme() -> Theme:
    return THEME
