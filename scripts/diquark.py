from abc import ABC, abstractmethod
from pathlib import Path
from typing import final, override

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
    output_path: Path,
    suu_mass: float,
    seed: int | None,
    delphes_card_path: Path | None = None,
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
        CommentCommand("NNPDF4.0 LO PDF set, with alpha_s = 0.118"),
        SetCommand("lhaid", "331900"),
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

    if seed is not None:
        commands += [
            CommentCommand("Fix the seed for reproducibility"),
            SetCommand("iseed", str(seed), card="run_card"),
        ]

    if delphes_card_path:
        commands.append(DelphesCardCommand(delphes_card_path.resolve()))
    else:
        commands += [
            CommentCommand("Use the default Delphes card for ATLAS"),
            DelphesCardCommand(
                output_path.resolve() / "Cards" / "delphes_card_ATLAS.dat"
            ),
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
    seed: int | None
    delphes_card_path: Path | None
    num_events: int

    def __init__(
        self,
        diquark_model_path: Path,
        output_path: Path,
        suu_mass: float,
        seed: int | None = None,
        delphes_card_path: Path | None = None,
        # 100.000 events is more than enough for the signal,
        # even though we'd have few counts in the real data.
        # It's enough for the ML algorithm.
        num_events: int = 100_000,
    ) -> None:
        self.diquark_model_path = diquark_model_path
        self.output_path = output_path
        self.suu_mass = suu_mass
        self.seed = seed
        self.delphes_card_path = delphes_card_path
        self.num_events = num_events

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

        commands += common_generation_commands(
            self.output_path,
            self.suu_mass,
            seed=self.seed,
            delphes_card_path=self.delphes_card_path,
        )

        commands += [
            CommentCommand("Generate a reasonable number of events"),
            SetCommand("nevents", str(self.num_events)),
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


class BackgroundProcessCommandsGenerator(CommandsGenerator, ABC):
    output_path: Path
    suu_mass: float
    seed: int | None
    delphes_card_path: Path | None
    num_events: int

    def __init__(
        self,
        output_path: Path,
        suu_mass: float,
        seed: int | None,
        delphes_card_path: Path | None,
        num_events: int = 500_000,
    ) -> None:
        self.output_path = output_path
        self.suu_mass = suu_mass
        self.seed = seed
        self.delphes_card_path = delphes_card_path

        assert num_events > 0, "Number of events must be positive"
        self.num_events = num_events

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

        commands += common_generation_commands(
            self.output_path,
            self.suu_mass,
            seed=self.seed,
            delphes_card_path=self.delphes_card_path,
        )

        commands += [
            CommentCommand("Generate a sufficient number of background events"),
            SetCommand("nevents", str(self.num_events)),
        ]

        return commands


@final
class QCDBackgroundGenerator(BackgroundProcessCommandsGenerator):
    max_jets: int

    def __init__(
        self,
        output_path: Path,
        suu_mass: float,
        max_jets: int,
        seed: int | None = None,
        delphes_card_path: Path | None = None,
        # Dominant background, we need to generate more events for it.
        num_events: int = 1_000_000,
    ) -> None:
        super().__init__(output_path, suu_mass, seed, delphes_card_path, num_events)
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
    max_extra_jets: int

    def __init__(
        self,
        output_path: Path,
        suu_mass: float,
        max_extra_jets: int,
        seed: int | None = None,
        delphes_card_path: Path | None = None,
        num_events: int = 500_000,
    ) -> None:
        super().__init__(output_path, suu_mass, seed, delphes_card_path, num_events)
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
    max_extra_jets: int

    def __init__(
        self,
        output_path: Path,
        suu_mass: float,
        max_extra_jets: int = 1,
        seed: int | None = None,
        delphes_card_path: Path | None = None,
        num_events: int = 300_000,
    ) -> None:
        super().__init__(output_path, suu_mass, seed, delphes_card_path, num_events)
        self.max_extra_jets = max_extra_jets

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        commands: list[MadGraphCommand] = [
            CommentCommand(
                "Define a new multiparticle for the two kinds of vector bosons"
            ),
            DefineCommand("v", "w+ w- z"),
        ]

        commands += [
            CommentCommand("Generate dibosons background"),
            GenerateProcessCommand(
                "p p > v v",
                subprocess_label="@0",
            ),
        ]

        for num_extra_jets in range(1, self.max_extra_jets + 1):
            extra_jets = " ".join("j" * num_extra_jets)
            commands.append(
                AddProcessCommand(
                    f"p p > v v {extra_jets}",
                    subprocess_label=f"@{num_extra_jets}",
                )
            )

        return commands
