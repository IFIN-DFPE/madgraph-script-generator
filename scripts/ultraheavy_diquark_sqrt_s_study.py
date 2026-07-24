"""This script generates MadGraph command files for studying the impact of
using only the sqrt(shat) min phase space cut.
"""

from pathlib import Path
from typing import Annotated, final, override

import typer

from madgraph_script_generator.commands import (
    CommentCommand,
    GenerateProcessCommand,
    MadGraphCommand,
    SetCommand,
)

from ultraheavy_diquark import (
    BackgroundProcessCommandsGenerator,
    SignalProcessCommandsGenerator,
)


@final
class QCDBackgroundGenerator(BackgroundProcessCommandsGenerator):
    num_jets: int
    sqrt_shat_min: float | None
    sqrt_shat_max: float | None

    def __init__(
        self,
        output_path: Path,
        sqrt_shat_min: float | None,
        sqrt_shat_max: float | None,
        num_jets: int,
        seed: int | None = None,
        num_events: int = 100_000,
    ) -> None:
        super().__init__(output_path, 0, seed, None, num_events)

        if num_jets > 4:
            raise Exception(
                "QCD with more than 4 jets is too expensive computationally"
            )

        self.sqrt_shat_min = sqrt_shat_min
        self.sqrt_shat_max = sqrt_shat_max
        self.num_jets = num_jets

    @override
    def _phase_space_cuts_commands(self, suu_mass: float) -> list[MadGraphCommand]:
        commands: list[MadGraphCommand] = [
            CommentCommand("=== Phase space cuts ==="),
        ]

        if self.sqrt_shat_min:
            q_scale = self.sqrt_shat_min
        elif self.sqrt_shat_max:
            q_scale = self.sqrt_shat_max
        else:
            q_scale = 0.4

        if self.sqrt_shat_min is not None:
            commands += (
                CommentCommand("Set a minimum invariant mass"),
                SetCommand("dsqrt_shat", f"{self.sqrt_shat_min:.0f}"),
            )

        if self.sqrt_shat_max is not None:
            commands += (
                CommentCommand("Set a maximum invariant mass"),
                SetCommand("dsqrt_shatmax", f"{self.sqrt_shat_max:.0f}"),
            )

        commands += (
            CommentCommand("Set a maximum pseudorapidity (eta) for the jets"),
            SetCommand("etaj", "2.5"),
            CommentCommand(
                "Set the xQCut threshold for merging; also sets the ptj and mmjj cuts"
            ),
            SetCommand("xqcut", f"{q_scale / 20:.0f}"),
        )

        return commands

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        jets = " ".join("j" * self.num_jets)

        commands: list[MadGraphCommand] = [
            CommentCommand("Generate QCD multijet background"),
            GenerateProcessCommand(f"p p > {jets}"),
        ]

        return commands


@final
class WBWB_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def _phase_space_cuts_commands(self, suu_mass: float) -> list[MadGraphCommand]:
        return []

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
        "simulations/diquark-sqrt-shat-study"
    ),
    seed: Annotated[int, typer.Option(help="Random seed for reproducibility")] = 123,
) -> None:
    output_directory = output_directory.resolve()

    sqrt_s_intervals: list[tuple[float | None, float | None]] = [
        (6000, 7500),
        (7500, 8500),
        (8500, None),
    ]

    for interval in sqrt_s_intervals:
        print(f"Generating scripts for sqrt(s_hat) min in the interval {interval}")
        low, high = interval

        run_name = ""
        if low is not None and high is not None:
            run_name = f"{low:.0f}_{high:.0f}"
        elif low is not None:
            run_name = f"{low:.0f}"
        elif high is not None:
            run_name = f"{high:.0f}"
        else:
            raise Exception("Cannot set both cuts to None")

        run_directory = output_directory / run_name

        scripts_output_directory = run_directory / "scripts"
        scripts_output_directory.mkdir(parents=True, exist_ok=True)
        madgraph_output_directory = run_directory / "data"

        # print("Generating script for S_{uu} -> \\chi \\chi -> Wb Wb process...")

        signal_name = "Suu_chichi_WbWb"

        signal_script_path = scripts_output_directory / f"{signal_name}.madgraph.txt"

        WBWB_ProcessCommandsGenerator(
            diquark_model_path,
            madgraph_output_directory / signal_name,
            suu_mass,
            seed=seed,
            num_events=100_000,
        ).save_to_file(signal_script_path)

        # print("Generating script for QCD multijet background...")
        for num_jets in range(2, 5):
            QCDBackgroundGenerator(
                madgraph_output_directory / f"qcd_2_to_{num_jets}",
                sqrt_shat_min=low,
                sqrt_shat_max=high,
                num_jets=num_jets,
                seed=seed,
                num_events=100_000,
            ).save_to_file(
                scripts_output_directory / f"qcd_2_to_{num_jets}.madgraph.txt"
            )


if __name__ == "__main__":
    typer.run(main)
