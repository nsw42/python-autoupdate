from pathlib import Path
import subprocess
from typing import Union

from .common import AutoupdateException, resolve_app_dir


class GitPullException(AutoupdateException):
    """
    Exception raised when git pull fails. Includes stdout and stderr from the git pull operation.
    """
    def __init__(self, message, stdout=None, stderr=None):
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(message)

    def __str__(self):
        if self.stdout or self.stderr:
            return f'{self.args[0]}\nstdout: {self.stdout}\nstderr: {self.stderr}'
        return f'{self.args[0]}'


def git_pull(app_dir: Union[str, Path, None] = None,
             git: str = 'git',
             timeout: int = 60):
    app_dir = resolve_app_dir(app_dir)
    child = subprocess.run([git, 'pull'], cwd=app_dir, capture_output=True, timeout=timeout, check=False, text=True)
    if child.returncode != 0:
        raise GitPullException("git pull failed", child.stdout, child.stderr)
