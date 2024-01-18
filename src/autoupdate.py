import logging
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Union
import __main__

import requests


class AutoupdateException(Exception):
    """
    Base class for all exceptions raised by the autoupdate library
    """


class NoAppDirException(AutoupdateException):
    """
    Exception raised when no application directory is specified, or a relative path was given,
    and no appropriate path can be found.
    """


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


class DownloadFailedException(AutoupdateException):
    """
    Exception raised when a download (i.e. requests.get) fails
    """


def default_app_dir() -> Path:
    if '__file__' not in dir(__main__):
        raise NoAppDirException("No path found for __main__")
    main = Path(__main__.__file__)
    return main.parent


def resolve_app_dir(app_dir: Union[str, Path, None]) -> Path:
    if app_dir is None:
        return default_app_dir()

    if not isinstance(app_dir, Path):
        app_dir = Path(app_dir)

    if not app_dir.is_absolute():
        app_dir = default_app_dir() / app_dir

    return app_dir


def resolve_file_path(app_dir: Path, file_path: Union[str, Path, None], default_leaf: str) -> Path:
    if file_path is None:
        return app_dir / default_leaf

    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    if file_path.is_absolute():
        return file_path

    return app_dir / file_path


def git_pull(app_dir: Union[str, Path, None] = None,
             git: str = 'git',
             timeout: int = 60):
    app_dir = resolve_app_dir(app_dir)
    child = subprocess.run([git, 'pull'], cwd=app_dir, capture_output=True, timeout=timeout, check=False, text=True)
    if child.returncode != 0:
        raise GitPullException("git pull failed", child.stdout, child.stderr)


def check_archive(url: str,
                  app_dir: Union[str, Path, None] = None,
                  version_file: Union[str, Path, None] = None,
                  timeout: int = 60):
    app_dir = resolve_app_dir(app_dir)
    version_file = resolve_file_path(app_dir, version_file, '.autoupdate.url')

    # Find where the URL points to
    response = requests.get(url, allow_redirects=False, timeout=timeout)
    if not response.ok:
        raise DownloadFailedException("Fetching URL failed")
    if not response.is_redirect:
        raise DownloadFailedException("URL did not result in a redirect")
    destination = response.headers['location']

    # Find out the current version
    if not version_file.is_file():
        current_version = None
    else:
        with open(version_file, encoding='utf8') as handle:
            current_version = handle.read().strip()

    # Check current vs available
    if destination == current_version:
        logging.debug(f"Latest available version is at {destination} which is already installed")

    with tempfile.TemporaryDirectory() as tempdir:
        # Fetch the new version
        with requests.get(destination, stream=True, timeout=timeout) as response:
            response.raise_for_status()
            tgz_path = Path(tempdir) / 'download.tgz'
            with open(tgz_path, 'wb') as handle:
                for chunk in response.iter_content(chunk_size=16384):
                    if chunk:
                        handle.write(chunk)

        # Extract it
        temp_app_dir = tempdir / app_dir.name
        shutil.unpack_archive(tgz_path, temp_app_dir)

        # Save the location for comparison next time around
        with open(temp_app_dir / version_file.name, 'w', encoding='utf8') as handle:
            handle.write(destination)

        # Move the current version of the application
        old_app_dir = app_dir.replace(app_dir.with_suffix('.bak'))

        # Move the new version into place
        temp_app_dir.replace(app_dir)

        # And now delete the old version
        shutil.rmtree(old_app_dir)
