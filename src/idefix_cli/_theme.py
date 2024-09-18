import sys
import unicodedata
from typing import Literal, TypedDict

if sys.version_info >= (3, 11):
    from typing import assert_never
else:
    from typing_extensions import assert_never


class Theme(TypedDict):
    LAUNCH: str
    SUCCESS: str
    WARNING: str
    ERROR: str
    HINT: str


Default = Theme(
    LAUNCH=unicodedata.lookup("ROCKET"),  # 🚀
    SUCCESS=unicodedata.lookup("PARTY POPPER"),  # 🎉
    WARNING=unicodedata.lookup("HEAVY EXCLAMATION MARK SYMBOL"),  # ❗
    ERROR=unicodedata.lookup("COLLISION SYMBOL"),  # 💥
    HINT=unicodedata.lookup("LEFT-POINTING MAGNIFYING GLASS"),  # 🔍
)

Baballe = Theme(
    LAUNCH=unicodedata.lookup("GUIDE DOG"),  # 🦮
    SUCCESS=unicodedata.lookup("POODLE"),  # 🐩
    WARNING=unicodedata.lookup("PAW PRINTS"),  # 🐾
    ERROR=unicodedata.lookup("HOT DOG"),  # 🌭
    HINT=unicodedata.lookup("CRYSTAL BALL"),  # 🔮
)


THEME = Default


def set_theme(theme: Literal["default", "baballe"]) -> None:
    global THEME
    if theme == "default":
        THEME = Default
    elif theme == "baballe":
        THEME = Baballe
    else:
        assert_never(theme)


def get_symbol(key: Literal["LAUNCH", "SUCCESS", "WARNING", "ERROR", "HINT"]) -> str:
    return THEME[key]
