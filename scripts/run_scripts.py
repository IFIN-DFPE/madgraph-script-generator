from __future__ import annotations
from collections.abc import Iterable
from pathlib import Path
import signal
import subprocess
from textwrap import dedent
from types import FrameType

from tqdm import tqdm
import typer

from madgraph_script_generator.runner import run_madgraph


def launch_slurm_jobs(script_file_paths: Iterable[Path], skip_existing: bool) -> None:
    for script_file_path in script_file_paths:
        script_file_path = script_file_path.resolve()
        script_name = script_file_path.name
        output_file_path = script_file_path.with_suffix(".log")

        if skip_existing and output_file_path.exists():
            print(
                f"Output file already exists for script {script_file_path}, skipping..."
            )
            continue

        print(f"Launching job for MadGraph script: {script_file_path}")
        print(f"Redirecting output to: {output_file_path}")

        slurm_script = dedent(f"""
        #!/usr/bin/env bash

        #SBATCH --nodes=1
        #SBATCH --cpus-per-task 256
        #SBATCH --time 08:00:00
        #SBATCH --job-name MadGraph_{script_name}

        mg5_aMC  {script_file_path} &> {output_file_path}
        """).strip()

        try:
            _ = subprocess.run("sbatch", input=slurm_script.encode("utf-8"), check=True)
        except Exception as err:
            print(
                f"An error occurred while launching Slurm job for MadGraph script {script_file_path}: {err}"
            )
            continue


def run_scripts(script_file_paths: Iterable[Path], skip_existing: bool) -> None:
    running_processes = set[subprocess.Popen[bytes]]()

    def signal_handler(signum: int, _: FrameType | None) -> None:
        if signum == signal.SIGINT or signum == signal.SIGTERM:
            for process in running_processes:
                try:
                    process.kill()
                except Exception as err:
                    print(f"An error occurred while killing a MadGraph process: {err}")
                    continue

            exit(0)

    # Set up various signal handlers to ensure that
    # all running MadGraph processes are killed when the script is interrupted or terminated.
    _ = signal.signal(signal.SIGINT, signal_handler)
    _ = signal.signal(signal.SIGTERM, signal_handler)

    for script_file_path in tqdm(script_file_paths, desc="Running MadGraph scripts"):
        output_file_path = script_file_path.with_suffix(".log")

        if skip_existing and output_file_path.exists():
            print(
                f"Output file already exists for script {script_file_path}, skipping..."
            )
            continue

        print(f"Running MadGraph script: {script_file_path}")
        print(f"Redirecting output to: {output_file_path}")

        try:
            run_madgraph(
                script_file_path,
                output_file_path,
                lambda process: running_processes.add(process),
            )

        except Exception as err:
            print(
                f"An error occurred while running MadGraph script {script_file_path}: {err}"
            )
            continue


def main(
    scripts_directory_path: Path,
    script_file_extension: str = ".madgraph.txt",
    skip_existing: bool = False,
    slurm: bool = False,
) -> None:
    if not scripts_directory_path.exists():
        print("Provided scripts directory doesn't exist")
        raise typer.Exit(code=1)

    if not scripts_directory_path.is_dir():
        print("Provided scripts directory path is not a directory")
        raise typer.Exit(code=1)

    print(f"Running MadGraph scripts from directory: {scripts_directory_path}")

    script_files = scripts_directory_path.glob(f"**/*{script_file_extension}")
    script_files = sorted(script_files)

    print(f"Found a total of {len(script_files)} script files to run")

    if slurm:
        print("Running each script as an independent job through SLURM")
        launch_slurm_jobs(script_files, skip_existing)
    else:
        print("Running scripts on local machine")
        run_scripts(script_files, skip_existing)


if __name__ == "__main__":
    typer.run(main)
