import inspect
from pathlib import Path
from typing import Union

from .common import resolve_app_dir
from .git import git_pull
from .archive import check_archive


def autoupdate(url: str,
               app_dir: Union[str, Path, None] = None,
               **kwargs):
    app_dir = resolve_app_dir(app_dir)
    git_dir = app_dir / '.git'
    if git_dir.is_dir():
        to_call = git_pull
    else:
        to_call = check_archive

    sig = inspect.signature(to_call)
    to_call_kwargs = {}
    for param_name, param in sig.parameters.items():
        if param_name == 'url':
            value = url
        elif param_name == 'app_dir':
            value = app_dir
        else:
            value = kwargs.get(param_name)
        to_call_kwargs[param_name] = value if value else param.default

    to_call(**to_call_kwargs)
