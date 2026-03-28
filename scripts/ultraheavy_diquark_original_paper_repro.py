"""This generation script uses the MG script generation toolkit
to reproduce the main results of the paper https://arxiv.org/abs/2503.17031.
"""

from pathlib import Path
import sys
from typing import Annotated, final, override

import typer

from madgraph_script_generator.commands import (
    GenerateProcessCommand,
    MadGraphCommand,
)

sys.path.append(str(Path(__file__).parent))
from diquark import (  # pyright: ignore[reportImplicitRelativeImport]
    SignalProcessCommandsGenerator,
    QCDBackgroundGenerator,
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
    seed: Annotated[int, typer.Option(help="Random seed for reproducibility")] = 123,
) -> None:
    output_directory = output_directory.resolve()
    output_directory = output_directory / f"Suu_{suu_mass:.1g}TeV"

    scripts_output_directory = output_directory / "scripts"
    madgraph_output_directory = output_directory / "data"

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
    ).save_to_file(signal_script_path)

    print("Generating MadGraph command scripts for background processes...")

    background_scripts_output_path = scripts_output_directory / "background"
    background_scripts_output_path.mkdir(parents=True, exist_ok=True)

    backgrounds_output_path = madgraph_output_directory / "background"

    QCDBackgroundGenerator(
        backgrounds_output_path / "qcd",
        suu_mass,
        max_jets=4,
        seed=seed,
    ).save_to_file(background_scripts_output_path / "qcd.madgraph.txt")

    TTBarBackgroundGenerator(
        backgrounds_output_path / "ttbar",
        suu_mass,
        max_extra_jets=2,
        seed=seed,
    ).save_to_file(background_scripts_output_path / "ttbar.madgraph.txt")

    DibosonBackgroundGenerator(
        backgrounds_output_path / "diboson",
        suu_mass,
        max_extra_jets=2,
        seed=seed,
    ).save_to_file(background_scripts_output_path / "diboson.madgraph.txt")


if __name__ == "__main__":
    typer.run(main)
