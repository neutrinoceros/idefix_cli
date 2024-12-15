import sys
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Literal, TypedDict

__all__ = ["get_symbol", "theme_ctx"]


class SymbolSet(TypedDict):
    LAUNCH: str
    SUCCESS: str
    WARNING: str
    ERROR: str
    HINT: str


@dataclass(frozen=True, slots=True, kw_only=True)
class Theme:
    name: str
    symbols: SymbolSet
    enter_msg: str | None
    exit_msg: str | None


class ThemeRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, Theme] = {}

    def register(
        self,
        name: str,
        *,
        symbols: SymbolSet,
        enter: str | None = None,
        exit: str | None = None,
    ):
        self._registry[name] = Theme(
            name=name, symbols=symbols, enter_msg=enter, exit_msg=exit
        )

    def __getitem__(self, item: str) -> Theme:
        return self._registry[item]


themes = ThemeRegistry()
themes.register(
    name="default",
    symbols={
        "LAUNCH": unicodedata.lookup("ROCKET"),  # 🚀
        "SUCCESS": unicodedata.lookup("PARTY POPPER"),  # 🎉
        "WARNING": unicodedata.lookup("HEAVY EXCLAMATION MARK SYMBOL"),  # ❗
        "ERROR": unicodedata.lookup("COLLISION SYMBOL"),  # 💥
        "HINT": unicodedata.lookup("LEFT-POINTING MAGNIFYING GLASS"),  # 🔍
    },
)

themes.register(
    name="baballe",
    symbols={
        "LAUNCH": unicodedata.lookup("GUIDE DOG"),  # 🦮
        "SUCCESS": unicodedata.lookup("POODLE"),  # 🐩
        "WARNING": unicodedata.lookup("PAW PRINTS"),  # 🐾
        "ERROR": unicodedata.lookup("HOT DOG"),  # 🌭
        "HINT": unicodedata.lookup("CRYSTAL BALL"),  # 🔮
    },
    enter=unicodedata.lookup("BASEBALL")
    + unicodedata.lookup("BLACK RIGHT-POINTING TRIANGLE"),
    exit=unicodedata.lookup("BLACK LEFT-POINTING TRIANGLE")
    + unicodedata.lookup("BASEBALL"),
)


THEME = themes["default"]


def get_symbol(key: Literal["LAUNCH", "SUCCESS", "WARNING", "ERROR", "HINT"]) -> str:
    return THEME.symbols[key]


@contextmanager
def theme_ctx(name: str):
    global THEME
    old_name = THEME.name
    THEME = themes[name]

    if THEME.enter_msg is not None:
        print(THEME.enter_msg, file=sys.stderr)
    try:
        yield
    finally:
        if THEME.exit_msg is not None:
            print(THEME.exit_msg, file=sys.stderr)

        THEME = themes[old_name]
