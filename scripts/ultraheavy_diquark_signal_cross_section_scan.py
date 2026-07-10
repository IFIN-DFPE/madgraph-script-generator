from abc import ABC
from pathlib import Path
import sys
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

sys.path.append(str(Path(__file__).parent))
from diquark import (  # pyright: ignore[reportImplicitRelativeImport]
    SignalProcessCommandsGenerator,
)


class SignalMassScanProcessCommandsGenerator(SignalProcessCommandsGenerator, ABC):
    "Base class for generating scripts which perform S_{uu} mass scans."

    suu_masses: list[float]

    def __init__(
        self,
        diquark_model_path: Path,
        output_path: Path,
        suu_masses: list[float],
        seed: int | None = None,
    ) -> None:
        super().__init__(
            diquark_model_path,
            output_path,
            suu_mass=0,
            seed=seed,
            delphes_card_path=None,
            num_events=0,
        )
        self.suu_masses = suu_masses
        del self.suu_mass

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

        for run_index, suu_mass in enumerate(self.suu_masses):
            assert 6 <= suu_mass <= 10

            commands += [
                CommentCommand(""),
                CommentCommand(f"===== Suu mass point: {suu_mass:.4g} TeV ====="),
                CommentCommand(""),
                LaunchCommand(
                    directory=self.output_path, run_name=f"MSuu_{suu_mass:.4g}_TeV"
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
                    CommentCommand("NNPDF4.0 LO PDF set, with alpha_s = 0.118"),
                    SetCommand("lhaid", "331900"),
                ]

                commands += [
                    CommentCommand("Set the collider energy, sqrt(s) = 13.6 TeV"),
                    SetCommand("ebeam1", "6800"),
                    SetCommand("ebeam2", "6800"),
                ]

                commands += [
                    CommentCommand("Disable systematic uncertainty calculation"),
                    SetCommand("use_syst", "F"),
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

            commands += self._phase_space_cuts_commands(suu_mass)

            commands += [
                CommentCommand(f"Mass of S_{{uu}} = {suu_mass:.4g} TeV"),
                SetCommand("MSuu", f"{suu_mass * 1000:.2f}"),
            ]

            commands += [
                CommentCommand(
                    "Recompute the widths for S_{uu} and \\chi, since the original model uses some hardcoded values which are not appropriate for our energy scale."
                ),
                ComputeWidthsCommand([9936661, 9936662]),
            ]

        commands.append(DoneCommand())

        return commands


@final
class WBWB_ProcessCommandsGenerator(SignalMassScanProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > w+ b, w+ > j j), (chi > w+ b, w+ > j j))"
            )
        ]


@final
class WBHT_ProcessCommandsGenerator(SignalMassScanProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > w+ b, w+ > j j), (chi > h t, (h > w+ w-, w+ > j j, w- > j j), (t > w+ b, w+ > j j)))"
            )
        ]


def main(
    diquark_model_path: Path = Path(
        # pyright: ignore[reportCallInDefaultInitializer]
        __file__
    ).parent
    / "diquarkVquark2023_UFO",
    output_directory: Path = Path(
        # pyright: ignore[reportCallInDefaultInitializer]
        "simulations/diquark-signal-cross-section-scan"
    ),
    seed: Annotated[int, typer.Option(help="Random seed for reproducibility")] = 42,
) -> None:
    output_directory = output_directory.resolve()

    scripts_output_directory = output_directory / "scripts"
    madgraph_output_directory = output_directory / "data"

    print("Generating MadGraph command script for signal process...")

    print("Generating script for S_{uu} -> \\chi \\chi -> Wb Wb process...")

    signal_name = "Suu_chichi_WbWb"

    wb_wb_signal_script_path = scripts_output_directory / f"{signal_name}.madgraph.txt"
    wb_wb_signal_script_path.parent.mkdir(parents=True, exist_ok=True)

    suu_masses: list[float] = [6.5, 6.75, 7.0, 7.25, 7.5, 8, 8.25, 8.5]

    WBWB_ProcessCommandsGenerator(
        diquark_model_path,
        madgraph_output_directory / signal_name,
        suu_masses,
        seed=seed,
    ).save_to_file(wb_wb_signal_script_path)

    signal_name = "Suu_chichi_Wbht"

    wb_ht_signal_script_path = scripts_output_directory / f"{signal_name}.madgraph.txt"

    WBHT_ProcessCommandsGenerator(
        diquark_model_path,
        madgraph_output_directory / signal_name,
        suu_masses,
        seed=seed,
    ).save_to_file(wb_ht_signal_script_path)


if __name__ == "__main__":
    typer.run(main)
