from pathlib import Path
import re
from typing import Annotated

from rich import print
import typer

from madgraph_script_generator.madgraph_logs import (
    NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN,
)

OUTPUT_PATH_REGEX: re.Pattern[str] = re.compile(
    r"Output to directory (/?(?:\S+/)+\S*) done\."
)


def extract_output_directory(contents: str) -> Path:
    "Extracts the output directory path from a MadGraph log file's contents."

    match: re.Match[str] | None = OUTPUT_PATH_REGEX.search(contents)
    if not match:
        raise Exception("Couldn't find output directory path mentioned in log file")

    return Path(match[1])


MATCHED_CROSS_SECTION_REGEX: re.Pattern[str] = re.compile(
    rf"Matched cross-section :\s*({NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN}) \+- ({NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN}) pb"
)


def extract_matched_cross_section(contents: str) -> float:
    "Extracts the matched cross-section from a MadGraph log file's contents."

    match: re.Match[str] | None = MATCHED_CROSS_SECTION_REGEX.search(contents)
    if not match:
        raise Exception("Couldn't find matched cross-section mentioned in log file")

    # matched_cross_section_error = float(match[2])

    return float(match[1])


def main(
    logs_directory: Annotated[
        Path, typer.Argument(help="Directory where to look for MadGraph log files")
    ],
) -> None:
    "Extracts information from MadGraph log files and prints it to the console."

    for log_file_path in logs_directory.glob("*.log"):
        print(f"Processing log file '{log_file_path}'")

        with open(log_file_path, "r") as file:
            contents = file.read()

        output_directory = extract_output_directory(contents)

        # TODO: handle multiple runs and/or different run names
        run_directory = output_directory / "Events" / "run_01"

        events_root_file_path = run_directory / "tag_1_delphes_events.root"
        print(f"ROOT file with events: {events_root_file_path}")

        matched_cross_section = extract_matched_cross_section(contents)
        print(
            f"Matched cross-section: [bold cyan]{matched_cross_section * 1000:2.3E}[/bold cyan] [cyan]fb[/cyan]"
        )

        print()


if __name__ == "__main__":
    typer.run(main)
