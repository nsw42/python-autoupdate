"""
common.py

Definitions common to updating via git pull and by downloading/unpacking archives
"""

from pathlib import Path
from typing import Union
import __main__


class AutoupdateException(Exception):
    """
    Base class for all exceptions raised by the autoupdate library
    """


class NoAppDirException(AutoupdateException):
    """
    Exception raised when no application directory is specified, or a relative path was given,
    and no appropriate path can be found.
    """


def default_app_dir() -> Path:
    if '__file__' not in dir(__main__):
        raise NoAppDirException("No path found for __main__")
    main = Path(__main__.__file__)
    return main.parent.resolve()


def resolve_app_dir(app_dir: Union[str, Path, None]) -> Path:
    if app_dir is None:
        return default_app_dir()

    if not isinstance(app_dir, Path):
        app_dir = Path(app_dir)

    if not app_dir.is_absolute():
        app_dir = default_app_dir() / app_dir

    return app_dir.resolve()
