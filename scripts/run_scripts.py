from pathlib import Path
import signal
import subprocess
from types import FrameType

from tqdm import tqdm
import typer

from madgraph_script_generator.runner import run_madgraph


def main(
    scripts_directory_path: Path, script_file_extension: str = ".madgraph.txt"
) -> None:
    if not scripts_directory_path.exists():
        print("Provided scripts directory doesn't exist")
        raise typer.Exit(code=1)

    if not scripts_directory_path.is_dir():
        print("Provided scripts directory path is not a directory")
        raise typer.Exit(code=1)

    print(f"Running MadGraph scripts from directory: {scripts_directory_path}")

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

    script_files = scripts_directory_path.glob(f"**/*{script_file_extension}")
    script_files = list(script_files)

    print(f"Found a total of {len(script_files)} script files to run")

    for script_file in tqdm(script_files, desc="Running MadGraph scripts"):
        output_file_path = script_file.with_suffix(".log")

        print(f"Running MadGraph script: {script_file}")
        print(f"Redirecting output to: {output_file_path}")

        run_madgraph(
            script_file,
            output_file_path,
            lambda process: running_processes.add(process),
        )


if __name__ == "__main__":
    typer.run(main)
