from pathlib import Path
import subprocess


def run_madgraph(script_file_path: Path, output_file_path: Path) -> None:
    """
    Runs MadGraph with the given script file.

    Args:
        script_file_path (Path): The path to the MadGraph script file.
        output_file_path (Path): The path to the output file where the MadGraph run log (standard output / standard error) will be saved.
    """
    # Ensure the script file exists
    if not script_file_path.is_file():
        raise FileNotFoundError(
            f"MadGraph script file doesn't exist or is not readable: {script_file_path}"
        )

    # Run MadGraph with the script
    try:
        with open(output_file_path, "w") as output_file:
            _ = subprocess.run(
                ["mg5_aMC", str(script_file_path)],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=output_file,
                stderr=subprocess.STDOUT,
            )
    except subprocess.CalledProcessError as err:
        print(f"An error occurred while running MadGraph: {err}")
