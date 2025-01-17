"""Contains code for scheduling and viewing PACE jobs."""

import re
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

from ampopt.utils import ampopt_path, parse_params, absolute


def run_pace_tuning_job(
    study: str,
    data: str,
    trials: int,
    pruner: str = "Median",
    sampler: str = "CmaEs",
    params: str = "",
    epochs: int = 100,
):
    params_dict = parse_params(params, prefix="param_")

    data = absolute(data, root="cwd")

    queue_job(
        "tune-amptorch-hyperparams",
        trials=trials,
        data=data,
        study=study,
        pruner=pruner,
        sampler=sampler,
        epochs=epochs,
        **params_dict,
    )


def to_path(job_name: str) -> Path:
    """Convert a job name to a filepath."""
    return ampopt_path / f"jobs/{job_name}.pbs"


def check_job_valid(job_name: str):
    """
    Raise AssertionError if either:
     - job_name doesn't exist, or
     - job_name's .pbs file has a different job name
    """
    config = to_path(job_name).read_text()
    match = re.search(r"^#PBS -N (.*?)$", config, re.M)
    assert match.group(1).strip() == job_name


def queue_job(job_name, **extra_args):
    """
    Schedule a job to be run.

    **extra_args are passed as environment variables to the job script.
    """
    path = to_path(job_name)
    extras = ",".join(f"{k}={v}" for k, v in extra_args.items())
    cmd = f"qsub {path}"
    if extras:
        cmd += f' -v "{extras}"'
    subprocess.run(cmd, shell=True)


def qstat():
    """
    Return the result of the command `qstat -u $USER -n1` command as a pandas DataFrame.

    This command returns a list of all the current user's jobs.
    """
    qstat_result = subprocess.run("qstat -u $USER -n1", shell=True, capture_output=True)
    data = [
        r.split()
        for r in qstat_result.stdout.decode("utf-8").splitlines()
        if r and r[0].isnumeric()
    ]
    columns = [
        "id",
        "username",
        "queue",
        "name",
        "sessid",
        "nds",
        "tsk",
        "memory",
        "time",
        "status",
        "elapsed",
        "node",
    ]
    df = pd.DataFrame(data, columns=columns)
    df["id"] = df["id"].apply(lambda x: x.split(".")[0])
    return df


def get_running_jobs(job_name: str = None):
    """
    Return pandas DataFrame consisting of current user's running or queued jobs whose
    name is `job_name`.

    If `job_name` is None, return all running jobs for current user.
    """
    jobs = qstat().query("status.isin(['Q', 'R'])")
    if job_name is not None:
        jobs = jobs[jobs.name == job_name]
    return jobs


def view_jobs(job_name: str = None):
    """
    Print current user's running or queued jobs whose name is `job_name`.

    If `job_name` is None, print all running or queued jobs for current user.
    """

    running_jobs = get_running_jobs(job_name=job_name)
    if len(running_jobs) == 0:
        if job_name is None:
            print("No running jobs.")
        else:
            print(f"No running jobs with name {job_name}.")
    else:
        print(running_jobs.to_string(index=False))


def get_or_start(job_name, just_queued=False):
    """
    Check if a job with name `job_name` is running, and if not queue it and wait for
    it to start.

    Return a pandas Series with information about the running job
    """
    check_job_valid(job_name)
    jobs = get_running_jobs(job_name)
    if len(jobs) == 1:
        job = jobs.iloc[0]
        if job.status == "Q":
            print(f"Waiting for {job_name} job {job.id} to start...")
            time.sleep(10)
            return get_or_start(job_name, just_queued=just_queued)
        print(f"{job_name} running, job ID: {job.id}")
        if just_queued:
            time.sleep(5)
        return job
    elif len(jobs) > 1:
        print(f"More than 1 {job_name} jobs running - aborting")
        sys.exit(1)
    else:
        print(f"Starting {job_name} job")
        queue_job(job_name)
        return get_or_start(job_name, just_queued=True)


def update_dotenv_file(node):
    """
    Update .env with information about the running MySQL job.
    """
    with open(ampopt_path / ".env") as f:
        lines = f.readlines()

    with open(ampopt_path / ".env", "w") as f:
        for line in lines:
            if not line.startswith("MYSQL_NODE"):
                f.write(line)
        f.write(f"MYSQL_NODE={node}")
