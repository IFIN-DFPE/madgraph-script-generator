import csv
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Annotated, final

import typer

from madgraph_script_generator.madgraph_logs import (
    MADGRAPH_RESULTS_SUMMARY_PATTERN,
    NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN,
)

RUN_NAME_PATTERN = re.compile(rf"MSuu_({NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN})_TeV")


@dataclass
@final
class RunInformation:
    suu_mass: float
    cross_section_pb: float
    cross_section_stddev_pb: float


def main(
    log_file_path: Annotated[Path, typer.Argument(help="Path to MadGraph log file")],
    csv_output_path: Annotated[
        Path | None,
        typer.Argument(
            help="Path where to dump extracted cross-sections in a CSV file"
        ),
    ] = None,
    no_print: Annotated[
        bool, typer.Option(help="Disable printing information to standard output")
    ] = False,
) -> None:
    with open(log_file_path, "r") as file:
        contents = file.read()

    seen = set[tuple[str, str]]()
    results = list[RunInformation]()

    matches: list[re.Match[str]] = MADGRAPH_RESULTS_SUMMARY_PATTERN.findall(contents)
    for match in matches:
        (
            run_name,
            tag,
            cross_section_pb,
            cross_section_stddev_pb,
            number_of_events,
        ) = match

        # Skip over duplicates (MadGraph tends to display the same information twice)
        identifier = run_name, tag
        if identifier in seen:
            continue

        seen.add(identifier)

        cross_section_pb = float(cross_section_pb)
        cross_section_stddev_pb = float(cross_section_stddev_pb)

        run_name_match = RUN_NAME_PATTERN.match(run_name)
        assert run_name_match is not None, "Run name doesn't match expected pattern"

        suu_mass = float(run_name_match[1])

        if not no_print:
            print(f'Run "{run_name}", tag "{tag}":')
            print(f"Ultraheavy scalar mass: {suu_mass} TeV")
            print(f"Cross section: {cross_section_pb} +/- {cross_section_stddev_pb} pb")
            print(f"Number of generated events: {number_of_events}")
            print()

        results.append(
            RunInformation(suu_mass, cross_section_pb, cross_section_stddev_pb)
        )

    if csv_output_path:
        with open(csv_output_path, mode="w", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=",")

            writer.writerow(("suu_mass", "cross_section_pb", "cross_section_stddev_pb"))

            for result in results:
                writer.writerow(
                    (
                        result.suu_mass,
                        result.cross_section_pb,
                        result.cross_section_stddev_pb,
                    )
                )

        print(f"Results saved to '{csv_output_path}'")


if __name__ == "__main__":
    typer.run(main)
