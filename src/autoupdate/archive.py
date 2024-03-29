import logging
from pathlib import Path
import shutil
import tempfile
from typing import Union

import requests

from .common import AutoupdateException, resolve_app_dir


class DownloadFailedException(AutoupdateException):
    """
    Exception raised when a download (i.e. requests.get) fails
    """


class ExtractException(AutoupdateException):
    """
    Exception raised when the downloaded file cannot be unpacked, or the contents don't match expectations
    """


def resolve_file_path(app_dir: Path, file_path: Union[str, Path, None], default_leaf: str) -> Path:
    if file_path is None:
        return app_dir / default_leaf

    if not isinstance(file_path, Path):
        file_path = Path(file_path)

    if file_path.is_absolute():
        return file_path

    return app_dir / file_path


def find_redirect_destination(url: str, timeout: int) -> str:
    response = requests.get(url, allow_redirects=False, timeout=timeout)
    if not response.ok:
        raise DownloadFailedException("Fetching URL failed")
    if not response.is_redirect:
        raise DownloadFailedException("URL did not result in a redirect")
    return response.headers['location']


def get_current_version(version_file: Path) -> Union[str, None]:
    if not version_file.is_file():
        return None

    with open(version_file, encoding='utf8') as handle:
        return handle.read().strip()


def download_archive(url: str, destination_path: Path, timeout: int):
    with requests.get(url, stream=True, timeout=timeout) as response:
        response.raise_for_status()
        with open(destination_path, 'wb') as handle:
            for chunk in response.iter_content(chunk_size=16384):
                if chunk:
                    handle.write(chunk)


def extract_archive(tempdir: Path,
                    tgz_path: Path,
                    archive_contains_app_dir: Union[bool, None]) -> Path:
    temp_app_dir = tempdir / 'unpack'
    try:
        shutil.unpack_archive(tgz_path, temp_app_dir)
    except ValueError as exc:
        raise ExtractException("Unable to extract downloaded file") from exc

    if archive_contains_app_dir is False:
        return temp_app_dir

    contents = list(temp_app_dir.glob('*'))
    n_contents = len(contents)

    if archive_contains_app_dir is None:
        if n_contents == 1 and contents[0].is_dir():
            temp_app_dir = contents[0]
    else:
        if n_contents != 1:
            raise ExtractException(f"Archive top-level directory contains {n_contents} items; expected exactly 1")
        temp_app_dir = contents[0]

    return temp_app_dir


def write_version_url_file(path: Path, url: str):
    with open(path, 'w', encoding='utf8') as handle:
        handle.write(url)


def check_archive(url: str,
                  app_dir: Union[str, Path, None] = None,
                  version_file: Union[str, Path, None] = None,
                  timeout: int = 60,
                  archive_contains_app_dir: Union[bool, None] = None):
    app_dir = resolve_app_dir(app_dir)
    version_file = resolve_file_path(app_dir, version_file, '.autoupdate.url')
    current_version = get_current_version(version_file)
    destination = find_redirect_destination(url, timeout)

    if destination == current_version:
        logging.debug(f"Latest available version is at {destination} which is already installed")
        return

    with tempfile.TemporaryDirectory() as tempdir:
        tempdir = Path(tempdir)

        tgz_path = tempdir / 'download.tgz'

        download_archive(destination, tgz_path, timeout)

        temp_app_dir = extract_archive(tempdir, tgz_path, archive_contains_app_dir)

        write_version_url_file(temp_app_dir / version_file.name, destination)

        # Move the current version of the application
        old_app_dir = app_dir.replace(app_dir.with_suffix('.bak'))

        # Move the new version into place
        temp_app_dir.replace(app_dir)

        # And now delete the old version
        shutil.rmtree(old_app_dir)
