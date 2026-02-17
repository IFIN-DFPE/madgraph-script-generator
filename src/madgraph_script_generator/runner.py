from pathlib import Path
import subprocess
from typing import Callable, Optional


def run_madgraph(
    script_file_path: Path,
    output_file_path: Path,
    process_created_callback: Optional[
        Callable[[subprocess.Popen[bytes]], None]
    ] = None,
) -> None:
    """
    Runs MadGraph with the given script file.

    Args:
        script_file_path: The path to the MadGraph script file.
        output_file_path: The path to the output file where the MadGraph run log (standard output / standard error) will be saved.
        process_created_callback: A callback function that will be called with the created MadGraph process.
    """
    # Ensure the script file exists
    if not script_file_path.is_file():
        raise FileNotFoundError(
            f"MadGraph script file doesn't exist or is not readable: {script_file_path}"
        )

    # Run MadGraph with the script
    try:
        with open(output_file_path, "w") as output_file:
            with subprocess.Popen(
                ["mg5_aMC", str(script_file_path)],
                stdin=subprocess.DEVNULL,
                stdout=output_file,
                stderr=subprocess.STDOUT,
            ) as process:
                if process_created_callback is not None:
                    process_created_callback(process)

            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, process.args)

    except subprocess.CalledProcessError as err:
        print(f"An error occurred while running MadGraph: {err}")
