from __future__ import annotations
import re
from pathlib import Path
from typing import Annotated

from rich import print
import typer

from madgraph_script_generator.madgraph_logs import (
    NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN,
)

OUTPUT_PATH_REGEX: re.Pattern[str] = re.compile(
    r"Output to directory (/?(?:\S+/)+\S*) done\."
)


def extract_output_directory(contents: str) -> Path | None:
    "Extracts the output directory path from a MadGraph log file's contents."

    matches: list[str] = OUTPUT_PATH_REGEX.findall(contents)
    if len(matches) == 0:
        return None

    if len(matches) > 1:
        raise Exception("Multiple runs in log file")

    match = matches[0]
    return Path(match)


MATCHED_CROSS_SECTION_REGEX: re.Pattern[str] = re.compile(
    rf"Matched cross-section :\s*({NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN}) \+- ({NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN}) pb"
)


def extract_matched_cross_section(contents: str) -> float | None:
    "Extracts the matched cross-section from a MadGraph log file's contents."

    matches: list[re.Match[str]] = MATCHED_CROSS_SECTION_REGEX.findall(contents)
    if len(matches) == 0:
        return None

    if len(matches) > 1:
        raise Exception("Multiple matched cross-sections found in log file")

    match = matches[0]

    # matched_cross_section_error = float(match[1])

    return float(match[0])


CROSS_SECTION_REGEX: re.Pattern[str] = re.compile(
    rf"Cross-section :\s*({NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN}) \+- ({NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN}) pb"
)


def extract_cross_section(contents: str) -> float | None:
    "Extracts the cross-section from a MadGraph log file's contents."

    matches: list[re.Match[str]] = CROSS_SECTION_REGEX.findall(contents)
    if len(matches) <= 1:
        return None

    if len(matches) > 2:
        raise Exception("Multiple results in same log file")

    match = matches[-1]
    return float(match[0])


def main(
    logs_directory: Annotated[
        Path, typer.Argument(help="Directory where to look for MadGraph log files")
    ],
) -> None:
    "Extracts information from MadGraph log files and prints it to the console."

    paths = list(logs_directory.glob("*.log"))
    paths = sorted(paths)

    for log_file_path in paths:
        print(f"Processing log file '{log_file_path}'")

        with open(log_file_path, "r") as file:
            contents = file.read()

        output_directory = extract_output_directory(contents)
        if output_directory:
            # TODO: handle multiple runs and/or different run names
            run_directory = output_directory / "Events" / "run_01"

            events_root_file_path = run_directory / "tag_1_delphes_events.root"
            print(f"ROOT file with events: {events_root_file_path}")

        else:
            print("[red]Couldn't extract run directory[/red]")

        matched_cross_section = extract_matched_cross_section(contents)
        if matched_cross_section:
            print(
                f"Matched cross-section: [bold cyan]{matched_cross_section * 1000:2.3E}[/bold cyan] [cyan]fb[/cyan]"
            )

        else:
            cross_section = extract_cross_section(contents)
            if cross_section:
                print(
                    f"Cross-section: [bold cyan]{cross_section * 1000:2.3E}[/bold cyan] [cyan]fb[/cyan]"
                )

            else:
                print("[red]Couldn't extract cross-section[/red]")

        print()


if __name__ == "__main__":
    typer.run(main)
