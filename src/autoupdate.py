from pathlib import Path
import subprocess
import __main__


class GitPullException(Exception):
    def __init__(self, message, stdout=None, stderr=None):
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(message)

    def __str__(self):
        if self.stdout or self.stderr:
            return f'{self.args[0]}\nstdout: {self.stdout}\nstderr: {self.stderr}'
        return f'{self.args[0]}'


def git_pull(repo_dir: str = None,
             git: str = 'git',
             timeout: int = 60):
    if repo_dir is None:
        if '__file__' not in dir(__main__):
            raise GitPullException("No path found for __main__")
        main = Path(__main__.__file__)
        repo_dir = main.parent
    child = subprocess.run([git, 'pull'], cwd=repo_dir, capture_output=True, timeout=timeout, check=False, text=True)
    if child.returncode != 0:
        raise GitPullException("git pull failed", child.stdout, child.stderr)
