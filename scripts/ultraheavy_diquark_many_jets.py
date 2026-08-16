"""Alternative fully-hadronic production routes for the ultraheavy diquark scalar
(with many jets in the final states), for the S_{uu} -> \\chi-\\chi channel.
"""

from enum import StrEnum
from pathlib import Path
from typing import Annotated, final, override

import typer

from madgraph_script_generator.commands import (
    AddProcessCommand,
    CommentCommand,
    GenerateProcessCommand,
    MadGraphCommand,
)

from ultraheavy_diquark import (
    BackgroundProcessCommandsGenerator,
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


@final
class CombinedBackgroundProcessesCommandsGenerator(BackgroundProcessCommandsGenerator):
    def __init__(
        self,
        output_path: Path,
        suu_mass: float,
        seed: int | None = None,
        delphes_card_path: Path | None = None,
        num_events: int = 2_000_000,
    ) -> None:
        super().__init__(output_path, suu_mass, seed, delphes_card_path, num_events)

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        # Start with QCD
        commands: list[MadGraphCommand] = [
            CommentCommand("Generate QCD 2->2"),
            GenerateProcessCommand("p p > j j"),
        ]

        for num_jets in range(3, 5):
            jets = " ".join("j" * num_jets)

            commands += [
                CommentCommand(f"Generate QCD 2->{num_jets}"),
                AddProcessCommand(f"p p > {jets}"),
            ]

        # Generate ttbar + jets
        for extra_jets in range(0, 3):
            jets = " ".join("j" * extra_jets)
            commands += [
                CommentCommand(f"Generate ttbar + {extra_jets} jets"),
                AddProcessCommand(f"p p > t t~{'' if extra_jets == 0 else ' ' + jets}"),
            ]

        # Generate single boson + jets
        for extra_jets in range(0, 2):
            jets = " ".join("j" * extra_jets)
            commands += [
                CommentCommand("Generate v + jets background"),
                GenerateProcessCommand(
                    f"p p > v{'' if extra_jets == 0 else ' ' + jets}, v > j j"
                ),
            ]

        # Generate diboson + jets
        for extra_jets in range(0, 2):
            jets = " ".join("j" * extra_jets)
            commands += [
                CommentCommand("Generate diboson + jets background"),
                GenerateProcessCommand(
                    f"p p > v v{'' if extra_jets == 0 else ' ' + jets}, v > j j"
                ),
            ]

        return commands


class BackgroundGenerationStrategy(StrEnum):
    GROUP_BY_PROCESS_TYPE = "group_by_process_type"
    ALL_TOGETHER = "all_together"


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
    include_signals_with_small_cross_sections: Annotated[
        bool,
        typer.Option(
            "--include-signals-with-small-cross-sections",
            help="Whether to include signals with small cross sections in the generation",
        ),
    ] = False,
    enable_pileup: Annotated[
        bool,
        typer.Option(
            "--pileup/--no-pileup",
            help="Whether to include pileup interactions in the generated samples",
        ),
    ] = False,
    background_generation_strategy: Annotated[
        BackgroundGenerationStrategy,
        typer.Option(help="Strategy for generating background processes"),
    ] = BackgroundGenerationStrategy.ALL_TOGETHER,
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

    signals_with_small_cross_sections = {
        "Suu_chichi_htht_wwt_wwt",
        "Suu_chichi_wbht_jjb_wwtt",
        "Suu_chichi_ztht_jjt_wwt",
    }

    if (
        background_generation_strategy
        == BackgroundGenerationStrategy.GROUP_BY_PROCESS_TYPE
    ):
        num_events_per_signal = 50_000 if small_sample else 200_000
    elif background_generation_strategy == BackgroundGenerationStrategy.ALL_TOGETHER:
        num_events_per_signal = 200_000 if small_sample else 1_000_000

    for signal_name, generator in signals.items():
        if (
            signal_name in signals_with_small_cross_sections
            and not include_signals_with_small_cross_sections
        ):
            print(
                f"Skipping signal {signal_name} due to small cross section (use --include-signals-with-small-cross-sections to include it)"
            )
            continue

        output_path = madgraph_output_directory / "signal" / signal_name

        generator(
            diquark_model_path,
            output_path,
            suu_mass,
            seed=seed,
            delphes_card_path=delphes_card,
            num_events=num_events_per_signal,
        ).save_to_file(signal_scripts_output_path / f"{signal_name}.madgraph.txt")

    print("Generating MadGraph command scripts for background processes...")

    background_scripts_output_path = scripts_output_directory / "background"
    background_scripts_output_path.mkdir(parents=True, exist_ok=True)

    backgrounds_output_path = madgraph_output_directory / "background"

    if (
        background_generation_strategy
        == BackgroundGenerationStrategy.GROUP_BY_PROCESS_TYPE
    ):
        qcd_counts: dict[int, int] = {
            2: 100_000,
            3: 200_000,
            4: 500_000,
            # 5: 500_000,
        }
        max_jets = max(qcd_counts.keys())

        for num_jets in range(2, max_jets):
            QCDBackgroundGenerator(
                backgrounds_output_path / f"qcd_2_to_{num_jets}",
                suu_mass,
                num_jets=num_jets,
                seed=seed,
                num_events=50_000 if small_sample else qcd_counts[num_jets],
            ).save_to_file(
                background_scripts_output_path / f"qcd_2_to_{num_jets}.madgraph.txt"
            )

        TTBarBackgroundGenerator(
            backgrounds_output_path / "ttbar",
            suu_mass,
            max_extra_jets=2,
            seed=seed,
            delphes_card_path=delphes_card,
            num_events=50_000 if small_sample else 200_000,
        ).save_to_file(background_scripts_output_path / "ttbar.madgraph.txt")

        SingleBosonBackgroundGenerator(
            backgrounds_output_path / "single_boson",
            suu_mass,
            max_extra_jets=1,
            seed=seed,
            delphes_card_path=delphes_card,
            num_events=50_000 if small_sample else 100_000,
        ).save_to_file(background_scripts_output_path / "single_boson.madgraph.txt")

        DibosonBackgroundGenerator(
            backgrounds_output_path / "diboson",
            suu_mass,
            max_extra_jets=1,
            seed=seed,
            delphes_card_path=delphes_card,
            num_events=50_000 if small_sample else 100_000,
        ).save_to_file(background_scripts_output_path / "diboson.madgraph.txt")

    elif background_generation_strategy == BackgroundGenerationStrategy.ALL_TOGETHER:
        CombinedBackgroundProcessesCommandsGenerator(
            backgrounds_output_path / "combined",
            suu_mass,
            seed=seed,
            delphes_card_path=delphes_card,
            num_events=200_000 if small_sample else 2_000_000,
        ).save_to_file(background_scripts_output_path / "combined.madgraph.txt")


if __name__ == "__main__":
    typer.run(main)
