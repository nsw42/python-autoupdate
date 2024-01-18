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

Note that there is not yet a mechanism for running any script as part of the update mechanism; any such needs (e.g. database schema migration) therefore needs to be handled as part of the application launcher.

## Application root directory

Whether the update is performed via git pull or unpacking a downloaded archive, the autoupdate needs to know the application directory.

For git pull, finding any directory within the application tree is sufficient because git then searches up the directory structure to find the `.git` directory, but if updating via an archive file then it's essential to correctly refer to the application root.

The autoupdate library uses a default value for the application directory of the directory containing the file that is the application entry point (i.e. `Path(__main__.__file__).parent`) but this can be overridden with the `app_dir` argument to the update call.

The `app_dir` parameter can be absolute (e.g. `/home/nsw42/myapp`) or relative (e.g. `..` to tell the autoupdater to go up an extra directory, which would be appropriate if the application was launched with `python app/src/main.py`).

If `app_dir` is not specified, or a relative path was given, and no appropriate path can be found (e.g. because the current environment is an interactive Python shell), then an `autoupdate.NoAppDirException` is raised.

## Update with git pull

From within your application:

```python
import autoupdate
...
autoupdate.git_pull()
```

That will use the defaults: using the default value for the application directory, relying on finding `git` on `$PATH`, and using a timeout of 60 seconds.

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

That will use the defaults for the update: finding where the URL redirects to, using the default value for the application directory, using a file `.autoupdate.url` inside the application root directory to store the current version, and a 60 second timeout.

These can be overriden:

```python
autoupdate.check_archive(url=''https://myapplication.com/latest',
                         app_dir='/home/nsw42/app',
                         version_file='/home/nsw42/.app.current_version_url',
                         timeout=300)
```

Note that the current version of the application is temporarily renamed with a `.bak` suffix; anything existing at that location will be deleted.
