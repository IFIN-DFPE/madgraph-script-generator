import csv
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Annotated, final

import typer

# Pattern for matching real numbers writing using scientific/exponential (E) notation.
# Taken from https://stackoverflow.com/a/658662/5723188
number_in_scientific_notation_pattern = r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+\-]?\d+)?"

# Regular expression for matching run summaries
# (with capture groups for run names, tags and cross-sections)
results_summary_pattern = re.compile(
    rf"""=== Results Summary for run: ((?:\w|\.)+) tag: ((?:\w|\.)+) ===
\s*Cross-section : \s*({number_in_scientific_notation_pattern})\s*\+-\s* ({number_in_scientific_notation_pattern}) pb
\s*Nb of events :  (\d+)""",
    re.MULTILINE,
)

run_name_pattern = re.compile(rf"MSuu_({number_in_scientific_notation_pattern})_TeV")


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

    matches: list[re.Match[str]] = results_summary_pattern.findall(contents)
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

        run_name_match = run_name_pattern.match(run_name)
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
