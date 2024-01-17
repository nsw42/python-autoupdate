# python-autoupdate

A python library to make it easier to update Python-based applications.

In reality, this is just a thin veneer over `subprocess.run(['git', 'pull'])`, but it also does the work of figuring out what directory to change to, before running git.

## Installation

Add a dependency to your requirements.txt:

```text
autoupdate@git+https://github.com/nsw42/python-autoupdate
```

## Usage

From within your application:

```python
import autoupdate
...
autoupdate.git_pull()
```

That will use the defaults for the update: performing an update in the directory where the application entry point (i.e. where `__main__`  was defined), assuming that `git` can be found on the path, and using a timeout of 60 seconds.

Any/all of these can be overridden:

```python
import autoupdate
...
autoupdate.git_pull(repo_dir='/home/nsw42/myapp',  # a Path object will actually work here, even though type hinting says a str is expected
                    git='/home/nsw42/bin/git',
                    timeout=3600)  # in seconds, so 3600 is an hour
```

## Error handling

If `repo_dir` is not specified, and no appropriate path can be found (e.g. because the current environment is an interactive Python shell), then an `autoupdate.GitPullException` is raised.

Also, if `git pull` exits non-zero, then an `autoupdate.GitPullException`, which will have `stdout` and `stderr` member variables containing the subprocess output.
