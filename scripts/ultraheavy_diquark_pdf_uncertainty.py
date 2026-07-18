from abc import ABC
from pathlib import Path
from typing import Annotated, final, override

import typer

from madgraph_script_generator.commands import (
    CommentCommand,
    ComputeWidthsCommand,
    DoneCommand,
    GenerateProcessCommand,
    ImportModelCommand,
    LaunchCommand,
    MadGraphCommand,
    OutputCommand,
    SetCommand,
    SetExternalToolsCommand,
)

from ultraheavy_diquark import (
    BackgroundProcessCommandsGenerator,
    PartonDistributionFunction,
    SignalProcessCommandsGenerator,
)
from ultraheavy_diquark.pdfs import (
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
)


class SignalPDFUncertaintyBenchmarkCommandsGenerator(
    SignalProcessCommandsGenerator, ABC
):
    "Base class for scripts which measure signal cross section uncertainty across multiple PDFs."

    pdfs: list[PartonDistributionFunction]

    def __init__(
        self,
        diquark_model_path: Path,
        output_path: Path,
        suu_mass: float,
        pdfs: list[PartonDistributionFunction],
        seed: int | None = None,
    ) -> None:
        super().__init__(
            diquark_model_path,
            output_path,
            suu_mass=suu_mass,
            seed=seed,
            delphes_card_path=None,
            num_events=0,
        )
        self.pdfs = pdfs

    @override
    def generate(self) -> list[MadGraphCommand]:
        commands = self._common_initial_commands()

        commands += [
            CommentCommand("Import BSM diquark model"),
            ImportModelCommand(self.diquark_model_path),
        ]

        commands += self.process_generation_commands()

        commands += [
            CommentCommand("Configure output directory"),
            OutputCommand(self.output_path),
        ]

        for run_index, pdf_set in enumerate(self.pdfs):
            commands += [
                CommentCommand(""),
                CommentCommand(
                    f"===== Parton Distribution Function (PDF): {pdf_set.name} ====="
                ),
                CommentCommand(""),
                LaunchCommand(
                    directory=self.output_path, run_name=f"pdf_{pdf_set.lhapdf_index}"
                ),
            ]

            # Common settings only need to be set/defined once
            if run_index == 0:
                commands += [
                    SetExternalToolsCommand(
                        analysis="MadAnalysis5", shower="Pythia8", detector="OFF"
                    ),
                    DoneCommand(),
                ]

                commands += [
                    CommentCommand("Use LHAPDF"),
                    SetCommand("pdlabel", "lhapdf"),
                ]

                commands += [
                    CommentCommand("Set the collider energy, sqrt(s) = 13.6 TeV"),
                    SetCommand("ebeam1", "6800"),
                    SetCommand("ebeam2", "6800"),
                ]

                commands += [
                    CommentCommand("Enable systematic uncertainty calculation"),
                    SetCommand("use_syst", "T"),
                ]

                commands += [
                    CommentCommand("Fix the seed for reproducibility"),
                    SetCommand("iseed", str(self.seed), card="run_card"),
                ]

                commands += [
                    CommentCommand(
                        "Generate a small number of events, since we only care about cross-sections"
                    ),
                    SetCommand("nevents", "1000"),
                ]

                commands += [
                    CommentCommand(
                        "Disable cuts on the decay products, since we will be applying them at the analysis level instead."
                    ),
                    SetCommand("cut_decays", "F"),
                ]

                commands += self._phase_space_cuts_commands(self.suu_mass)

                commands += [
                    CommentCommand(f"Mass of S_{{uu}} = {self.suu_mass:.4g} TeV"),
                    SetCommand("MSuu", f"{self.suu_mass * 1000:.2f}"),
                ]

                commands += [
                    CommentCommand(
                        "Recompute the widths for S_{uu} and \\chi, since the original model uses some hardcoded values which are not appropriate for our energy scale."
                    ),
                    ComputeWidthsCommand([9936661, 9936662]),
                ]

            commands += [
                CommentCommand(pdf_set.name),
                SetCommand("lhaid", pdf_set.lhapdf_index),
            ]

        commands.append(DoneCommand())

        return commands


@final
class WBHT_ProcessCommandsGenerator(SignalPDFUncertaintyBenchmarkCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > w+ b, w+ > j j), (chi > h t, (h > b b~), (t > w+ b, w+ > j j)))"
            )
        ]


class BackgroundPDFUncertaintyBenchmarkCommandsGenerator(
    BackgroundProcessCommandsGenerator, ABC
):
    "Base class for scripts which measure background cross-secgion uncertainty across multiple PDFs."

    pdfs: list[PartonDistributionFunction]

    def __init__(
        self,
        output_path: Path,
        suu_mass: float,
        pdfs: list[PartonDistributionFunction],
        seed: int | None = None,
    ) -> None:
        super().__init__(
            output_path,
            suu_mass=suu_mass,
            seed=seed,
            delphes_card_path=None,
            num_events=1000,
        )
        self.pdfs = pdfs

    @override
    def generate(self) -> list[MadGraphCommand]:
        commands = self._common_initial_commands()

        commands += self.process_generation_commands()

        commands += [
            CommentCommand("Configure output directory"),
            OutputCommand(self.output_path),
        ]

        for run_index, pdf_set in enumerate(self.pdfs):
            commands += [
                CommentCommand(""),
                CommentCommand(
                    f"===== Parton Distribution Function (PDF): {pdf_set.name} ====="
                ),
                CommentCommand(""),
                LaunchCommand(
                    directory=self.output_path, run_name=f"pdf_{pdf_set.lhapdf_index}"
                ),
            ]

            # Common settings only need to be set/defined once
            if run_index == 0:
                commands += [
                    SetExternalToolsCommand(
                        analysis="MadAnalysis5", shower="Pythia8", detector="OFF"
                    ),
                    DoneCommand(),
                ]

                commands += [
                    CommentCommand("Use LHAPDF"),
                    SetCommand("pdlabel", "lhapdf"),
                ]

                commands += [
                    CommentCommand("Set the collider energy, sqrt(s) = 13.6 TeV"),
                    SetCommand("ebeam1", "6800"),
                    SetCommand("ebeam2", "6800"),
                ]

                commands += [
                    CommentCommand("Enable systematic uncertainty calculation"),
                    SetCommand("use_syst", "T"),
                ]

                commands += [
                    CommentCommand("Fix the seed for reproducibility"),
                    SetCommand("iseed", str(self.seed), card="run_card"),
                ]

                commands += [
                    CommentCommand(
                        "Generate a small number of events, since we only care about cross-sections"
                    ),
                    SetCommand("nevents", "1000"),
                ]

                commands += self._phase_space_cuts_commands(self.suu_mass)

            commands += [
                CommentCommand(pdf_set.name),
                SetCommand("lhaid", pdf_set.lhapdf_index),
            ]

        commands.append(DoneCommand())

        return commands


@final
class QCDBackgroundPDFUncertaintyBenchmarkCommandsGenerator(
    BackgroundPDFUncertaintyBenchmarkCommandsGenerator
):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            CommentCommand("Generate QCD 2->2 background"),
            GenerateProcessCommand("p p > j j"),
        ]


def main(
    diquark_model_path: Path = Path(
        # pyright: ignore[reportCallInDefaultInitializer]
        __file__
    ).parent
    / "diquarkVquark2023_UFO",
    suu_mass: Annotated[
        float, typer.Option(help="Mass of the S_{uu} diquark scalar in TeV")
    ] = 8.0,
    output_directory: Path = Path(
        # pyright: ignore[reportCallInDefaultInitializer]
        "simulations/diquark-pdf-uncertainty"
    ),
    seed: Annotated[int, typer.Option(help="Random seed for reproducibility")] = 42,
) -> None:
    output_directory = output_directory.resolve()

    scripts_output_directory = output_directory / "scripts"
    madgraph_output_directory = output_directory / "data"

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

    print("Generating script for S_{uu} -> \\chi \\chi -> Wb ht process...")

    signal_name = "Suu_chichi_Wbht"

    wb_ht_signal_script_path = scripts_output_directory / f"{signal_name}.madgraph.txt"
    wb_ht_signal_script_path.parent.mkdir(parents=True, exist_ok=True)

    WBHT_ProcessCommandsGenerator(
        diquark_model_path,
        madgraph_output_directory / signal_name,
        suu_mass,
        pdfs_list,
        seed,
    ).save_to_file(wb_ht_signal_script_path)

    print("Generating script for QCD 2 -> 2 background process...")

    background_name = "qcd_2_to_2"

    background_script_path = (
        scripts_output_directory / f"{background_name}.madgraph.txt"
    )
    background_script_path.parent.mkdir(parents=True, exist_ok=True)

    QCDBackgroundPDFUncertaintyBenchmarkCommandsGenerator(
        madgraph_output_directory / background_name,
        suu_mass,
        pdfs_list,
        seed,
    ).save_to_file(background_script_path)


if __name__ == "__main__":
    typer.run(main)
