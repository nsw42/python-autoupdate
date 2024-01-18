# python-autoupdate

A python library to make it easier to update Python-based applications.

## Installation

Add a dependency to your requirements.txt:

```text
autoupdate@git+https://github.com/nsw42/python-autoupdate
```

## Usage

The autoupdate library offers two different mechanisms for updating an application.

The first relies on the application being a `git clone` of some repository; the autoupdate is then a thin veneer over `subprocess.run(['git', 'pull'])`, but it also does the work of figuring out what directory to change to, before running git.

The alternative approach relies on the ability to access a constant URL e.g. `https://myapplication.com/latest`, which redirects to an archive file (e.g. `.tar.gz` or `.zip`); the autoupdate then unpacks the archive, and replaces the current application directory with the unpacked version.

Note that there is not yet a mechanism for running any script (e.g. to perform database schema migration) as part of the update mechanism; any such activity therefore needs to be handled as part of the application launcher.

## Application root directory

Whether the update is performed via git pull or unpacking a downloaded archive, the autoupdate needs to know the application directory.

For git pull, finding anywhere within the application tree is sufficient because git then searches up the directory structure to find the `.git` directory, but if updating via an archive file then it's essential to correctly refer to the application root.

The autoupdate library uses a default value for the application directory of the directory containing the file that is the application entry point but this can be overridden with the `app_dir` argument to the update call. (For example, if the application is launched as `python app/main.py`, then `app` is the application root directory)

The `app_dir` parameter can be absolute (e.g. `/home/nsw42/myapp`) or relative (e.g. `..` to tell the autoupdater to go up an extra directory, which would be appropriate if the application was launched with `python app/src/main.py`).

If `app_dir` is not specified, or a relative path was given, and no appropriate path can be found (e.g. because the current environment is an interactive Python shell), then an `autoupdate.NoAppDirException` is raised.

## Update with git pull

From within your application:

```python
import autoupdate
...
autoupdate.git_pull()
```

That will use the defaults: the default application directory, relying on finding `git` on `$PATH`, and using a timeout of 60 seconds.

Any/all of these can be overridden:

```python
autoupdate.git_pull(app_dir='/home/nsw42/myapp',
                    git='/home/nsw42/bin/git',
                    timeout=3600)  # in seconds, so 3600 is an hour
```

### Error handling

If `git pull` exits non-zero, then an `autoupdate.GitPullException` is raised, which will have `stdout` and `stderr` member variables containing the subprocess output.

## Update from archive file

From within your application:

```python
import autoupdate
...
autoupdate.check_archive('https://myapplication.com/latest')
```

That will use the defaults for the update: the default application directory, using a file `.autoupdate.url` inside the application root directory to store the current version, a 60 second timeout on download operations, and automatically detects whether the archive contains the new application directory or the application itself.

These can be overriden:

```python
autoupdate.check_archive(url='https://myapplication.com/latest',
                         app_dir='/home/nsw42/app',
                         version_file='/home/nsw42/.app.current_version_url',
                         timeout=300,
                         archive_contains_app_dir=True)
```

Note that the current version of the application is temporarily renamed with a `.bak` suffix during the upgrade process; anything existing at that location will be deleted.

### Archive contents format

The archive of an application can take one of two formats: either, the archive can contain an application directory, which in turn contains the application itself, or the archive can contain the application contents without an intermediate directory. These alternatives are shown-below:

With an application directory:

```text
app.zip
    app_dir/
        main.py
        resources/
            image.png
        utils.py
```

Without an application directory:

```text
app.zip
    main.py
    resources/
        image.png
    utils.py
```

The `archive_contains_app_dir` parameter to `check_archive` indicates what the update should expect:

* `None`: the library automatically detects whether the archive contains an application directory: if the top-level of the archive consists of a single item, which is a directory, then that is treated as the application directory; if there is more than one item in the top-level of the archive, or the single item is a file, then it is assumed that the archive contents are the replacement for the application directory contents.
* `True`: the archive is expected to contain a single top-level directory; an `autoupdate.ExtractException` is raised if that is not true. The directory is then moved into place as the new application root directory.
* `False`: the archive is expected to contain the application contents themselves; this is only likely to be useful if the application contents are deliberately nested inside an extra directory, and it is desired to keep that directory.

### check_archive arguments

* `url` (`str`): the URL to fetch, which is expected to return a redirect to an archive file (any file format that can be extracted by `shutil.unpack_archive`)
* `app_dir` (`str`, `Path` or `None`): the application root directory, as explained above
* `version_file` (`str`, `Path` or `None`): a file that records the URL of the most recently downloaded version. If specified, the path can be relative (to the application root directory), or absolute; if not specified, a file `.autoupdate.url` inside the application root directory is used.
* `timeout` (int): the timeout, in seconds, to use for each request (firstly, downloading the constant URL, and secondly downloading the archive itself).
* `archive_contains_app_dir` (`True`, `False` or `None`): whether the archive contains the application, including a new application root directory, or just the application contents. See 'Archive contents format', above.
