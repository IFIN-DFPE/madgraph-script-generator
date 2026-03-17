"""Alternative fully-hadronic production routes for the ultraheavy diquark scalar
(with many jets in the final states).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import final, override

import typer

from madgraph_script_generator.commands import (
    AddProcessCommand,
    CommentCommand,
    ComputeWidthsCommand,
    DefineCommand,
    DelphesCardCommand,
    DoneCommand,
    GenerateProcessCommand,
    ImportModelCommand,
    LaunchCommand,
    MadGraphCommand,
    OutputCommand,
    SetCommand,
    SetExternalToolsCommand,
    write_commands_to_file,
)


def common_initial_commands() -> list[MadGraphCommand]:
    commands: list[MadGraphCommand] = []

    commands += [
        CommentCommand("Configure parallelism"),
        SetCommand("run_mode", "2"),
        SetCommand("nb_core", "120"),
    ]

    commands += [
        CommentCommand("Import the Standard Model"),
        ImportModelCommand("sm-full"),
    ]

    return commands


def phase_space_cuts_commands(suu_mass: float) -> list[MadGraphCommand]:
    return [
        CommentCommand("=== Phase space cuts ==="),
        SetCommand("dsqrt_shat", f"{(suu_mass - 0.5) * 1000:.0f}"),
    ]


def common_generation_commands(
    output_path: Path, suu_mass: float, seed: int = 17
) -> list[MadGraphCommand]:
    commands: list[MadGraphCommand] = []

    commands += [
        SetExternalToolsCommand(
            analysis="MadAnalysis5", shower="Pythia8", detector="Delphes"
        ),
        DoneCommand(),
    ]

    commands += [
        CommentCommand("Use LHAPDF"),
        SetCommand("pdlabel", "lhapdf"),
        CommentCommand("NNPDF4.0 aN3LO"),
        SetCommand("lhaid", "336700"),
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
        CommentCommand("=== Jet matching and merging ==="),
        CommentCommand("Enable MLM matching scheme"),
        SetCommand("ickkw", "1"),
        CommentCommand("ME-PS boundary is at 100 GeV"),
        SetCommand("xqcut", "100.0"),
    ]

    commands += phase_space_cuts_commands(suu_mass)

    commands += [
        CommentCommand("Fix the seed for reproducibility"),
        SetCommand("iseed", str(seed), card="run_card"),
    ]

    commands += [
        CommentCommand("Use the default Delphes card for ATLAS"),
        DelphesCardCommand(output_path.resolve() / "Cards" / "delphes_card_ATLAS.dat"),
    ]

    return commands


class CommandsGenerator(ABC):
    @abstractmethod
    def generate(self) -> list[MadGraphCommand]: ...

    def save_to_file(self, path: Path) -> None:
        write_commands_to_file(path, self.generate())


class SignalProcessCommandsGenerator(CommandsGenerator, ABC):
    diquark_model_path: Path
    output_path: Path
    suu_mass: float

    def __init__(
        self, diquark_model_path: Path, output_path: Path, suu_mass: float
    ) -> None:
        self.diquark_model_path = diquark_model_path
        self.output_path = output_path
        self.suu_mass = suu_mass

    @abstractmethod
    def process_generation_commands(self) -> list[MadGraphCommand]: ...

    @override
    def generate(self) -> list[MadGraphCommand]:
        commands = common_initial_commands()

        commands += [
            CommentCommand("Import BSM diquark model"),
            ImportModelCommand(self.diquark_model_path),
        ]

        commands += self.process_generation_commands()

        commands += [
            CommentCommand("Configure output directory"),
            OutputCommand(self.output_path),
        ]

        commands.append(LaunchCommand())

        commands += common_generation_commands(self.output_path, self.suu_mass)

        commands += [
            CommentCommand("Generate a reasonable number of events"),
            SetCommand("nevents", "100000"),
        ]

        commands += [
            CommentCommand(f"Mass of S_{{uu}} = {self.suu_mass} TeV"),
            SetCommand("MSuu", f"{self.suu_mass * 1000:.0f}"),
        ]

        commands += [
            CommentCommand(
                "Disable cuts on the decay products, since we will be applying them at the analysis level instead."
            ),
            SetCommand("cut_decays", "F"),
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
class HTHT_WWTWWT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > h t, h > w+ w-), (chi > h t, h > w+ w-))"
            )
        ]


@final
class HTHT_BBTBBT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > h t, h > b b~), (chi > h t, h > b b~))"
            )
        ]


@final
class WBZT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > w+ b), (chi > z t))"
            )
        ]


@final
class WBHT_JJBWWT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > w+ b, w+ > j j), (chi > h t, h > w+ w-))"
            )
        ]


@final
class WBHT_JJBBBT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > w+ b, w+ > j j), (chi > h t, h > b b~))"
            )
        ]


@final
class ZTZT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > z t), (chi > z t))"
            )
        ]


@final
class ZTHT_JJTWWT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > z t, z > j j), (chi > h t, h > w+ w-))"
            )
        ]


@final
class ZTHT_JJTBBT_ProcessCommandsGenerator(SignalProcessCommandsGenerator):
    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        return [
            GenerateProcessCommand(
                "p p > suu, (suu > chi chi, (chi > z t, z > j j), (chi > h t, h > b b~))"
            )
        ]


class BackgroundProcessCommandsGenerator(CommandsGenerator, ABC):
    output_path: Path
    suu_mass: float

    def __init__(self, output_path: Path, suu_mass: float) -> None:
        self.output_path = output_path
        self.suu_mass = suu_mass

    @abstractmethod
    def process_generation_commands(self) -> list[MadGraphCommand]: ...

    @override
    def generate(self) -> list[MadGraphCommand]:
        commands = common_initial_commands()

        commands += self.process_generation_commands()

        commands += [
            CommentCommand("Configure output directory"),
            OutputCommand(self.output_path),
        ]

        commands.append(LaunchCommand())

        commands += common_generation_commands(self.output_path, self.suu_mass)

        commands += [
            CommentCommand("Generate a sufficient number of background events"),
            SetCommand("nevents", "50000"),
        ]

        return commands


@final
class QCDBackgroundGenerator(BackgroundProcessCommandsGenerator):
    def __init__(self, output_path: Path, suu_mass: float, max_jets: int) -> None:
        super().__init__(output_path, suu_mass)
        self.max_jets = max_jets

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        commands: list[MadGraphCommand] = [
            CommentCommand("Generate QCD multijet background"),
            GenerateProcessCommand(
                "p p > j j",
                subprocess_label="@0" if self.max_jets > 2 else None,
            ),
        ]

        for num_jets in range(3, self.max_jets + 1):
            jets_str = " ".join("j" * num_jets)
            commands.append(
                AddProcessCommand(
                    f"p p > {jets_str}".strip(),
                    subprocess_label=f"@{num_jets - 2}",
                )
            )

        return commands


@final
class TTBarBackgroundGenerator(BackgroundProcessCommandsGenerator):
    def __init__(self, output_path: Path, suu_mass: float, max_extra_jets: int) -> None:
        super().__init__(output_path, suu_mass)
        self.max_extra_jets = max_extra_jets

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        commands: list[MadGraphCommand] = [
            CommentCommand("Generate t tbar background"),
            GenerateProcessCommand(
                "p p > t t~",
                subprocess_label="@0" if self.max_extra_jets > 0 else None,
            ),
        ]

        for num_extra_jets in range(1, self.max_extra_jets + 1):
            extra_jets = " ".join("j" * num_extra_jets)
            commands.append(
                AddProcessCommand(
                    f"p p > t t~ {extra_jets}",
                    subprocess_label=f"@{num_extra_jets}",
                )
            )

        return commands


@final
class DibosonBackgroundGenerator(BackgroundProcessCommandsGenerator):
    def __init__(self, output_path: Path, suu_mass: float) -> None:
        super().__init__(output_path, suu_mass)

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        commands: list[MadGraphCommand] = [
            CommentCommand("Define a new multiparticle for the two types of W boson"),
            DefineCommand("w", "w+ w-"),
        ]

        commands += [
            CommentCommand("Generate dibosons background"),
            GenerateProcessCommand(
                "p p > w+ w-",
                subprocess_label="@0",
            ),
        ]

        commands.append(
            AddProcessCommand(
                "p p > w z",
                subprocess_label="@1",
            )
        )

        commands.append(
            AddProcessCommand(
                "p p > z z",
                subprocess_label="@2",
            )
        )

        return commands


def main(
    diquark_model_path: Path = Path(
        # pyright: ignore[reportCallInDefaultInitializer]
        __file__
    ).parent
    / "diquarkVquark2023_UFO",
    scripts_output_directory: Path = Path(
        # pyright: ignore[reportCallInDefaultInitializer]
        "diquark-many-jets/scripts"
    ),
    madgraph_output_directory: Path = Path(
        # pyright: ignore[reportCallInDefaultInitializer]
        "diquark-many-jets/data"
    ),
) -> None:
    scripts_output_directory = scripts_output_directory.resolve()
    madgraph_output_directory = madgraph_output_directory.resolve()

    # For now, we generate scripts only for a single possible mass of the diquark scalar
    suu_mass = 8.0  # TeV

    print("Generating MadGraph command script for signal processes...")

    signal_scripts_output_path = scripts_output_directory / "signal"
    signal_scripts_output_path.mkdir(parents=True, exist_ok=True)

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

        generator(diquark_model_path, output_path, suu_mass).save_to_file(
            signal_scripts_output_path / f"{full_signal_name}.madgraph.txt"
        )

    print("Generating MadGraph command scripts for background processes...")

    background_scripts_output_path = scripts_output_directory / "background"
    background_scripts_output_path.mkdir(parents=True, exist_ok=True)

    backgrounds_output_path = madgraph_output_directory / "background"

    QCDBackgroundGenerator(
        backgrounds_output_path / "qcd_multijet",
        suu_mass,
        4,
    ).save_to_file(background_scripts_output_path / "qcd_multijet.madgraph.txt")

    TTBarBackgroundGenerator(
        backgrounds_output_path / "ttbar_multijet", suu_mass, 2
    ).save_to_file(background_scripts_output_path / "ttbar_multijet.madgraph.txt")

    DibosonBackgroundGenerator(
        backgrounds_output_path / "diboson", suu_mass
    ).save_to_file(background_scripts_output_path / "diboson.madgraph.txt")


if __name__ == "__main__":
    typer.run(main)
