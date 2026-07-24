"""Alternative fully-hadronic production routes for the ultraheavy diquark scalar
(with many jets in the final states).
"""

from pathlib import Path
from typing import Annotated, final, override

import typer

from madgraph_script_generator.commands import (
    GenerateProcessCommand,
    MadGraphCommand,
)

from ultraheavy_diquark import (
    SignalProcessCommandsGenerator,
    QCDBackgroundGenerator,
    TTBarBackgroundGenerator,
    DibosonBackgroundGenerator,
    SingleBosonBackgroundGenerator,
)


@final
class HTHT_WWTWWT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > h t, (h > w+ w-, w+ > j j, w- > j j), (t > w+ b, w+ > j j)), (chi > h t, (h > w+ w-, w+ > j j, w- > j j), (t > w+ b, w+ > j j)))"
            )
        ]


@final
class HTHT_BBTBBT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > h t, (h > b b~), (t > w+ b, w+ > j j)), (chi > h t, (h > b b~), (t > w+ b, w+ > j j)))"
            )
        ]


@final
class WBZT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > w+ b, w+ > j j), (chi > h t, (h > b b~), (t > w+ b, w+ > j j)))"
            )
        ]


@final
class WBHT_JJBWWT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > w+ b, w+ > j j), (chi > h t, (h > w+ w-, w+ > j j, w- > j j), (t > w+ b, w+ > j j)))"
            )
        ]


@final
class WBHT_JJBBBT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > w+ b, w+ > j j), (chi > h t, (h > b b~), (t > w+ b, w+ > j j)))"
            )
        ]


@final
class ZTZT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > z t, (z > j j), (t > w+ b, w+ > j j)), (chi > z t, (z > j j), (t > w+ b, w+ > j j))) "
            )
        ]


@final
class ZTHT_JJTWWT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > z t, z > j j, (t > w+ b, w+ > j j)), (chi > h t, (h > w+ w-, w+ > j j, w- > j j), (t > w+ b, w+ > j j)))"
            )
        ]


@final
class ZTHT_JJTBBT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > z t, (z > j j), (t > w+ b, w+ > j j)), (chi > h t, (h > b b~), (t > w+ b, w+ > j j)))"
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
        "simulations/diquark-many-jets"
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
    seed: Annotated[int, typer.Option(help="Random seed for reproducibility")] = 42,
) -> None:
    output_directory = output_directory.resolve()
    output_directory = output_directory / f"Suu_{suu_mass:.1g}TeV"

    scripts_output_directory = output_directory / "scripts"
    madgraph_output_directory = output_directory / "data"

    print("Generating MadGraph command script for signal processes...")

    signal_scripts_output_path = scripts_output_directory / "signal"
    signal_scripts_output_path.mkdir(parents=True, exist_ok=True)

    delphes_card: Path | None = None
    if enable_pileup:
        delphes_card = Path(
            "/data/gmajeri/diquark-simulations/pileup/delphes_card_ATLAS_PileUp.tcl"
        )

    signals: dict[str, type[SignalProcessCommandsGenerator]] = {
        "Suu_chichi_htht_wwt_wwt": HTHT_WWTWWT_ProcessCommandsGenerator,
        "Suu_chichi_htht_bbt_bbt": HTHT_BBTBBT_ProcessCommandsGenerator,
        "Suu_chichi_wbzt": WBZT_ProcessCommandsGenerator,
        "Suu_chichi_wbht_jjb_wwtt": WBHT_JJBWWT_ProcessCommandsGenerator,
        "Suu_chichi_wbht_jjb_bbt": WBHT_JJBBBT_ProcessCommandsGenerator,
        "Suu_chichi_ztzt": ZTZT_ProcessCommandsGenerator,
        "Suu_chichi_ztht_jjt_wwt": ZTHT_JJTWWT_ProcessCommandsGenerator,
        "Suu_chichi_ztht_jjt_bbt": ZTHT_JJTBBT_ProcessCommandsGenerator,
    }

    for signal_name, generator in signals.items():
        full_signal_name = f"{signal_name}_{suu_mass:.1g}TeV"
        output_path = madgraph_output_directory / "signal" / full_signal_name

        generator(
            diquark_model_path,
            output_path,
            suu_mass,
            seed=seed,
            delphes_card_path=delphes_card,
            num_events=50_000 if small_sample else 100_000,
        ).save_to_file(signal_scripts_output_path / f"{full_signal_name}.madgraph.txt")

    print("Generating MadGraph command scripts for background processes...")

    background_scripts_output_path = scripts_output_directory / "background"
    background_scripts_output_path.mkdir(parents=True, exist_ok=True)

    backgrounds_output_path = madgraph_output_directory / "background"

    for num_jets in range(2, 6):
        QCDBackgroundGenerator(
            backgrounds_output_path / f"qcd_2_to_{num_jets}",
            suu_mass,
            num_jets=num_jets,
            seed=seed,
            num_events=50_000 if small_sample else 200_000,
        ).save_to_file(
            background_scripts_output_path / f"qcd_2_to_{num_jets}.madgraph.txt"
        )

    TTBarBackgroundGenerator(
        backgrounds_output_path / "ttbar",
        suu_mass,
        max_extra_jets=2,
        seed=seed,
        delphes_card_path=delphes_card,
        num_events=50_000 if small_sample else 600_000,
    ).save_to_file(background_scripts_output_path / "ttbar.madgraph.txt")

    SingleBosonBackgroundGenerator(
        backgrounds_output_path / "single_boson",
        suu_mass,
        max_extra_jets=1,
        seed=seed,
        delphes_card_path=delphes_card,
        num_events=50_000 if small_sample else 150_000,
    ).save_to_file(background_scripts_output_path / "single_boson.madgraph.txt")

    DibosonBackgroundGenerator(
        backgrounds_output_path / "diboson",
        suu_mass,
        max_extra_jets=1,
        seed=seed,
        delphes_card_path=delphes_card,
        num_events=50_000 if small_sample else 300_000,
    ).save_to_file(background_scripts_output_path / "diboson.madgraph.txt")


if __name__ == "__main__":
    typer.run(main)
