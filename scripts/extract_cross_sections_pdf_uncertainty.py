import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
import re
import sys
from typing import Annotated, final

import typer

from madgraph_script_generator.madgraph_logs import (
    MADGRAPH_RESULTS_SUMMARY_PATTERN,
    NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN,
)

sys.path.append(str(Path(__file__).parent))
from diquark import (  # pyright: ignore[reportImplicitRelativeImport]
    PDF_MSHT20_LO_AS_130,
    PDF_MSHT20_NNLO_AS_118,
    PDF_NNPDF23_LO_AS_0119_QED,
    PDF_NNPDF23_LO_AS_0130_QED,
    PDF_NNPDF23_NNLO_AS_0118,
    PDF_NNPDF30_LO_AS_0118,
    PDF_NNPDF31_LO_AS_0118,
    PDF_NNPDF31_LO_AS_0130,
    PDF_NNPDF40_LO_AS_01180,
    PDF_NNPDF40_NNLO_AS_01180,
    PartonDistributionFunction,
)

RUN_NAME_PATTERN = re.compile(r"pdf_(\d+)")

PDF_VARIATION_PATTERN = re.compile(
    rf"# PDF variation:\s*(\+{NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN})%\s*(-{NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN})%"
)


@dataclass
@final
class RunInformation:
    pdf_name: str
    lhapdf_index: str
    alpha_strong: Decimal
    cross_section_pb: float
    cross_section_stddev_pb: float
    pdf_variation_percentage_above: float
    pdf_variation_percentage_below: float


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

    pdf_variation_matches: list[re.Match[str]] = PDF_VARIATION_PATTERN.findall(contents)
    index = 0

    pdfs_list: list[PartonDistributionFunction] = [
        PDF_NNPDF23_LO_AS_0130_QED,
        PDF_NNPDF23_LO_AS_0119_QED,
        PDF_NNPDF23_NNLO_AS_0118,
        PDF_NNPDF30_LO_AS_0118,
        PDF_NNPDF31_LO_AS_0130,
        PDF_NNPDF31_LO_AS_0118,
        PDF_NNPDF40_LO_AS_01180,
        PDF_NNPDF40_NNLO_AS_01180,
        PDF_MSHT20_LO_AS_130,
        PDF_MSHT20_NNLO_AS_118,
    ]

    pdfs_by_index: dict[str, PartonDistributionFunction] = {
        pdf.lhapdf_index: pdf for pdf in pdfs_list
    }

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

        lhapdf_index = str(run_name_match[1])

        pdf = pdfs_by_index.get(lhapdf_index)

        if not pdf:
            raise Exception(f"Couldn't find PDF matching LHAPDF index '{lhapdf_index}'")

        pdf_variation = pdf_variation_matches[index]
        pdf_variation_percentage_above = float(pdf_variation[0])
        pdf_variation_percentage_below = abs(float(pdf_variation[1]))

        if not no_print:
            print(f'Run "{run_name}", tag "{tag}":')
            print(f"Parton Distribution Function: {pdf.name} TeV")
            print(f"Cross section: {cross_section_pb} +/- {cross_section_stddev_pb} pb")
            print(f"Number of generated events: {number_of_events}")
            print(
                f"PDF variation: +{pdf_variation_percentage_above}% -{pdf_variation_percentage_below}%"
            )
            print()

        index += 1

        results.append(
            RunInformation(
                pdf.name,
                pdf.lhapdf_index,
                pdf.alpha_strong,
                cross_section_pb,
                cross_section_stddev_pb,
                pdf_variation_percentage_above,
                pdf_variation_percentage_below,
            )
        )

    if csv_output_path:
        with open(csv_output_path, mode="w", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=",")

            writer.writerow(
                (
                    "pdf_name",
                    "pdf_lhapdf_index",
                    "alpha_strong",
                    "cross_section_pb",
                    "cross_section_stddev_pb",
                    "pdf_variation_percentage_above",
                    "pdf_variation_percentage_below",
                )
            )

            for result in results:
                writer.writerow(
                    (
                        result.pdf_name,
                        result.lhapdf_index,
                        result.alpha_strong,
                        result.cross_section_pb,
                        result.cross_section_stddev_pb,
                        result.pdf_variation_percentage_above,
                        -result.pdf_variation_percentage_below,
                    )
                )

        print(f"Results saved to '{csv_output_path}'")


if __name__ == "__main__":
    typer.run(main)
