from pathlib import Path

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

    script_files = scripts_directory_path.glob(f"**/*{script_file_extension}")
    script_files = list(script_files)

    print(f"Found a total of {len(script_files)} script files to run")

    for script_file in tqdm(script_files, desc="Running MadGraph scripts"):
        output_file_path = script_file.with_suffix(".madgraph.log")

        print(f"Running MadGraph script: {script_file}")
        print(f"Redirecting output to: {output_file_path}")

        run_madgraph(script_file, output_file_path)


if __name__ == "__main__":
    typer.run(main)
