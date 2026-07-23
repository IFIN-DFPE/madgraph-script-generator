"""This generation script uses the MG script generation toolkit
to reproduce the main results of the paper https://arxiv.org/abs/2503.17031.
"""

from enum import Enum
from pathlib import Path
from typing import Annotated, final, override

import typer

from madgraph_script_generator.commands import (
    GenerateProcessCommand,
    MadGraphCommand,
)

from ultraheavy_diquark import (
    Pythia8BackgroundProcessGenerator,
    SignalProcessCommandsGenerator,
    QCDMultijetBackgroundGenerator,
    TTBarBackgroundGenerator,
    DibosonBackgroundGenerator,
)


@final
class WBWB_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > w+ b, w+ > j j), (chi > w+ b, w+ > j j))"
            )
        ]


class BackgroundGenerationStrategy(str, Enum):
    GROUP_BY_PROCESS = "group_by_process"
    INDIVIDUAL_PROCESSES = "individual_processes"


PYTHIA8_PROCESSES: dict[str, str] = {
    "gg_bbar": "g g > b b~",
    "gg_ccbar": "g g > c c~",
    "gg_gg": "g g > g g",
    "qqbar_gg": "q q~ > g g",
    "gg_qqbar": "g g > q q~",
    "qg_qg": "q g > q g",
    "qqbar_bbbar": "q q~ > b b~",
    "qqbar_ccbar": "q q~ > c c~",
    "qq_qq": "q q > q q",
    "qqbar_qqbar": "q q~ > q q~",
    "gg_Hg": "g g > h g",
    "ff_HZ": "f f~ > h z",
    "ff_HW": "f f~ > h w+",
    "ff_Hff": "f f~ > h f f~",
    "ff_Hff2": "f f > h f f",
    "gg_Httbar": "g g > h t t~",
    "qq_Httbar": "q q~ > h t t~",
    "qg_Hq": "q g > h q",
    "ffbar_Wgm": "f f~ > w+ g",
    "ffbar_WZ": "f f~ > w+ z",
    "ffbar_WW": "f f~ > w+ w-",
    "ffbar_Wff": "f f~ > w+ f f~",
}


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
        "simulations/diquark-repro"
    ),
    small_sample: Annotated[
        bool,
        typer.Option(
            "--small",
            "--testing",
            help="Whether to generate a small sample for testing",
        ),
    ] = False,
    enable_pileup: Annotated[
        bool,
        typer.Option(
            "--pileup/--no-pileup",
            help="Whether to include pileup interactions in the generated samples",
        ),
    ] = False,
    generate_background: Annotated[
        bool,
        typer.Option(
            "--with-background/--no-background",
            help="Whether to also generate scripts for the background processes.",
        ),
    ] = False,
    background_generation_strategy: Annotated[
        BackgroundGenerationStrategy,
        typer.Option(help="Strategy for generating background processes"),
    ] = BackgroundGenerationStrategy.GROUP_BY_PROCESS,
    seed: Annotated[int, typer.Option(help="Random seed for reproducibility")] = 123,
) -> None:
    output_directory = output_directory.resolve()
    output_directory = output_directory / f"Suu_{suu_mass:.1g}TeV"

    scripts_output_directory = output_directory / "scripts"
    madgraph_output_directory = output_directory / "data"

    delphes_card: Path | None = None
    if enable_pileup:
        delphes_card = Path(
            "/data/gmajeri/diquark-simulations/pileup/delphes_card_ATLAS_PileUp.tcl"
        )

    print("Generating MadGraph command script for signal process...")

    print("Generating script for S_{uu} -> \\chi \\chi -> Wb Wb process...")

    signal_name = f"Suu_chichi_WbWb_MSuu_{suu_mass:.1g}TeV"

    signal_script_path = (
        scripts_output_directory / "signal" / f"{signal_name}.madgraph.txt"
    )
    signal_script_path.parent.mkdir(parents=True, exist_ok=True)

    WBWB_ProcessCommandsGenerator(
        diquark_model_path,
        madgraph_output_directory / "signal" / signal_name,
        suu_mass,
        seed=seed,
        delphes_card_path=delphes_card,
        num_events=50_000 if small_sample else 1_000_000,
    ).save_to_file(signal_script_path)

    if not generate_background:
        return

    print("Generating MadGraph command scripts for background processes...")

    background_scripts_output_path = scripts_output_directory / "background"
    background_scripts_output_path.mkdir(parents=True, exist_ok=True)

    backgrounds_output_path = madgraph_output_directory / "background"

    if background_generation_strategy == BackgroundGenerationStrategy.GROUP_BY_PROCESS:
        print("Generating MadGraph scripts for backgrounds grouped by process type...")

        print("Generating script for QCD multijet background...")
        QCDMultijetBackgroundGenerator(
            backgrounds_output_path / "qcd",
            suu_mass,
            max_jets=4,
            seed=seed,
            delphes_card_path=delphes_card,
            num_events=50_000 if small_sample else 500_000,
        ).save_to_file(background_scripts_output_path / "qcd.madgraph.txt")

        print("Generating script for top-antitop background...")
        TTBarBackgroundGenerator(
            backgrounds_output_path / "ttbar",
            suu_mass,
            max_extra_jets=2,
            seed=seed,
            delphes_card_path=delphes_card,
            num_events=50_000 if small_sample else 500_000,
        ).save_to_file(background_scripts_output_path / "ttbar.madgraph.txt")

        print("Generating script for diboson pairs background...")
        DibosonBackgroundGenerator(
            backgrounds_output_path / "diboson",
            suu_mass,
            max_extra_jets=2,
            seed=seed,
            delphes_card_path=delphes_card,
            num_events=50_000 if small_sample else 500_000,
        ).save_to_file(background_scripts_output_path / "diboson.madgraph.txt")

    elif (
        background_generation_strategy
        == BackgroundGenerationStrategy.INDIVIDUAL_PROCESSES
    ):
        print("Generating MadGraph scripts for individual background processes...")

        for process_name, process_definition in PYTHIA8_PROCESSES.items():
            print(f"Generating script for {process_name} process...")

            process_output_path = backgrounds_output_path / process_name
            Pythia8BackgroundProcessGenerator(
                process_definition,
                process_output_path,
                suu_mass,
                seed=seed,
                delphes_card_path=delphes_card,
                num_events=50_000 if small_sample else 100_000,
            ).save_to_file(
                background_scripts_output_path / f"{process_name}.madgraph.txt"
            )

    else:
        raise ValueError(  # pyright: ignore[reportUnreachable]
            f"Invalid background generation strategy: {background_generation_strategy}"
        )


if __name__ == "__main__":
    typer.run(main)
