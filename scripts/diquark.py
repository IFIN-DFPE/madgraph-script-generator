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


def vector_boson_multiparticle_definition_commands() -> list[MadGraphCommand]:
    "Returns the commands for defining a new multiparticle `v`, representing a vector boson."

    return [
        CommentCommand("Define a new multiparticle for the two kinds of vector bosons"),
        DefineCommand("v", "w+ w- z"),
    ]


class CommandsGenerator(ABC):
    @abstractmethod
    def generate(self) -> list[MadGraphCommand]: ...

    def save_to_file(self, path: Path) -> None:
        write_commands_to_file(path, self.generate())

    def _common_initial_commands(
        self,
        include_pythia8_particle_definitions: bool = False,
    ) -> list[MadGraphCommand]:
        commands: list[MadGraphCommand] = []

        commands += [
            CommentCommand("Configure parallelism"),
            SetCommand("run_mode", "2"),
            SetCommand("nb_core", "100"),
        ]

        if not isinstance(self, SignalProcessCommandsGenerator):
            commands += [
                CommentCommand("Import the full Standard Model"),
                ImportModelCommand("sm-full"),
            ]

        if include_pythia8_particle_definitions:
            commands += [
                CommentCommand(
                    "Define a new multiparticle for quarks, matching the Pythia8 definition of the q multiparticle."
                ),
                DefineCommand("q", "u c d s b"),
                DefineCommand("q~", "u~ c~ d~ s~ b~"),
                DefineCommand("f", "u c d s b"),
                DefineCommand("f~", "u~ c~ d~ s~ b~"),
            ]

        return commands

    def _phase_space_cuts_commands(self, suu_mass: float) -> list[MadGraphCommand]:
        commands: list[MadGraphCommand] = [
            CommentCommand("=== Phase space cuts ==="),
            CommentCommand(
                "Set the center-of-mass energy for the cuts, to be slightly below the S_{uu} mass to avoid cutting into the signal phase space."
            ),
            SetCommand("dsqrt_shat", f"{(suu_mass - 0.5) * 1000:.0f}"),
            CommentCommand("Set the minimum sum of pTs of the jets."),
            SetCommand("htjmin", f"{suu_mass / 4 * 1000:.0f}"),
            # CommentCommand("Set the minimum pT of any jet."),
            # SetCommand("ptj", f"{suu_mass / 16 * 1000:.0f}"),
        ]

        return commands

    def _common_generation_commands(
        self,
        output_path: Path,
        suu_mass: float,
        # xqcut_value_gev: float = 30.0,
        seed: int | None = None,
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
            # CommentCommand("NNPDF 2.3 QCD + QED LO PDF set, with alpha_s = 0.130"),
            # SetCommand("lhaid", "247000"),
        ]

        commands += [
            CommentCommand("Set the collider energy, sqrt(s) = 13.6 TeV"),
            SetCommand("ebeam1", "6800"),
            SetCommand("ebeam2", "6800"),
        ]

        commands += [
            # CommentCommand("Enable systematic uncertainty calculation"),
            # SetCommand("use_syst", "T"),
            CommentCommand("Disable systematic uncertainty calculation"),
            SetCommand("use_syst", "F"),
        ]

        # commands += [
        #     CommentCommand("Disable jet matching"),
        #     SetCommand("ickkw", "0"),
        #     CommentCommand(f"ME-PS boundary is at {xqcut_value_gev} GeV"),
        #     SetCommand("xqcut", str(xqcut_value_gev)),
        # ]

        commands += self._phase_space_cuts_commands(suu_mass)

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

        # Not needed, they are "on" by default.
        # commands += [
        #     CommentCommand("Enable MPI, ISR and FSR in Pythia"),
        #     SetCommand("PartonLevel:MPI", "on", card="pythia8_card"),
        #     SetCommand("PartonLevel:ISR", "on", card="pythia8_card"),
        #     SetCommand("PartonLevel:FSR", "on", card="pythia8_card"),
        # ]

        return commands


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

        commands.append(LaunchCommand())

        commands += self._common_generation_commands(
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
                "Recompute the widths for t/t~, h0, S_{uu} and \\chi, since the original model uses some hardcoded values which are not appropriate for our energy scale."
            ),
            ComputeWidthsCommand([6, 25, 9936661, 9936662]),
        ]

        commands.append(DoneCommand())

        return commands


class BackgroundProcessCommandsGenerator(CommandsGenerator, ABC):
    output_path: Path
    suu_mass: float
    seed: int | None
    delphes_card_path: Path | None
    num_events: int
    include_pythia8_particle_definitions: bool

    def __init__(
        self,
        output_path: Path,
        suu_mass: float,
        seed: int | None,
        delphes_card_path: Path | None,
        num_events: int,
    ) -> None:
        self.output_path = output_path
        self.suu_mass = suu_mass
        self.seed = seed
        self.delphes_card_path = delphes_card_path

        assert num_events > 0, "Number of events must be positive"
        self.num_events = num_events

        self.include_pythia8_particle_definitions = False

    @abstractmethod
    def process_generation_commands(self) -> list[MadGraphCommand]: ...

    @override
    def generate(self) -> list[MadGraphCommand]:
        commands = self._common_initial_commands(
            include_pythia8_particle_definitions=self.include_pythia8_particle_definitions
        )

        commands += self.process_generation_commands()

        commands += [
            CommentCommand("Configure output directory"),
            OutputCommand(self.output_path),
        ]

        commands.append(LaunchCommand())

        commands += self._common_generation_commands(
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
class Pythia8BackgroundProcessGenerator(BackgroundProcessCommandsGenerator):
    process: str

    def __init__(
        self,
        process: str,
        output_path: Path,
        suu_mass: float,
        seed: int | None = None,
        delphes_card_path: Path | None = None,
        # Less events per invidiual background process,
        # since there are many of them.
        num_events: int = 50_000,
    ) -> None:
        super().__init__(output_path, suu_mass, seed, delphes_card_path, num_events)
        self.process = process
        self.include_pythia8_particle_definitions = True

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        commands: list[MadGraphCommand] = [
            CommentCommand("Generate background using Pythia8's built-in processes"),
            GenerateProcessCommand(self.process),
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
        num_events: int = 500_000,
    ) -> None:
        super().__init__(output_path, suu_mass, seed, delphes_card_path, num_events)

        if max_jets > 4:
            raise Exception(
                "QCD with more than 4 jets is too expensive computationally"
            )

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
        num_events: int = 300_000,
    ) -> None:
        super().__init__(output_path, suu_mass, seed, delphes_card_path, num_events)
        self.max_extra_jets = max_extra_jets

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        commands: list[MadGraphCommand] = [
            CommentCommand("Generate t tbar background"),
            GenerateProcessCommand(
                "p p > t t~, (t > w+ b, w+ > j j), (t~ > w- b~, w- > j j)",
                subprocess_label="@0" if self.max_extra_jets > 0 else None,
            ),
        ]

        for num_extra_jets in range(1, self.max_extra_jets + 1):
            extra_jets = " ".join("j" * num_extra_jets)
            commands.append(
                AddProcessCommand(
                    f"p p > t t~ {extra_jets}, (t > w+ b, w+ > j j), (t~ > w- b~, w- > j j)",
                    subprocess_label=f"@{num_extra_jets}",
                )
            )

        return commands


@final
class TTBarPlusHiggsBackgroundGenerator(BackgroundProcessCommandsGenerator):
    max_extra_jets: int

    def __init__(
        self,
        output_path: Path,
        suu_mass: float,
        max_extra_jets: int,
        seed: int | None = None,
        delphes_card_path: Path | None = None,
        num_events: int = 300_000,
    ) -> None:
        super().__init__(output_path, suu_mass, seed, delphes_card_path, num_events)
        self.max_extra_jets = max_extra_jets

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        decays: list[str] = ["h > b b~", "h > v v, v > j j"]

        commands: list[MadGraphCommand] = (
            vector_boson_multiparticle_definition_commands()
        )

        commands += [
            CommentCommand("Generate t tbar + Higgs background"),
            CommentCommand(""),
        ]

        index = 0

        for higgs_decay in decays:
            commands.append(CommentCommand(f"Processes with {higgs_decay} decay"))

            for num_extra_jets in range(0, self.max_extra_jets + 1):
                if num_extra_jets > 0:
                    extra_jets = " " + " ".join("j" * num_extra_jets)
                else:
                    extra_jets = ""

                process = f"p p > t t~ h{extra_jets}, (t > w+ b, w+ > j j), (t~ > w- b~, w- > j j), ({higgs_decay})"
                subprocess_label = f"@{index}"

                if index == 0:
                    commands.append(GenerateProcessCommand(process, subprocess_label))
                else:
                    commands.append(AddProcessCommand(process, subprocess_label))

                index += 1

        return commands


@final
class BBBarPlusHiggsBackgroundGenerator(BackgroundProcessCommandsGenerator):
    max_extra_jets: int

    def __init__(
        self,
        output_path: Path,
        suu_mass: float,
        max_extra_jets: int,
        seed: int | None = None,
        delphes_card_path: Path | None = None,
        num_events: int = 300_000,
    ) -> None:
        super().__init__(output_path, suu_mass, seed, delphes_card_path, num_events)
        self.max_extra_jets = max_extra_jets

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        decays: list[str] = ["h > b b~", "h > v v, v > j j"]

        commands: list[MadGraphCommand] = (
            vector_boson_multiparticle_definition_commands()
        )

        commands += [
            CommentCommand("Generate b bbar + Higgs background"),
            CommentCommand(""),
        ]

        index = 0

        for higgs_decay in decays:
            commands.append(CommentCommand(f"Processes with {higgs_decay} decay"))

            for num_extra_jets in range(0, self.max_extra_jets + 1):
                if num_extra_jets > 0:
                    extra_jets = " " + " ".join("j" * num_extra_jets)
                else:
                    extra_jets = ""

                process = f"p p > b b~ h{extra_jets}, ({higgs_decay})"
                subprocess_label = f"@{index}"

                if index == 0:
                    commands.append(GenerateProcessCommand(process, subprocess_label))
                else:
                    commands.append(AddProcessCommand(process, subprocess_label))

                index += 1

        return commands


@final
class HiggsBackgroundGenerator(BackgroundProcessCommandsGenerator):
    max_extra_jets: int

    def __init__(
        self,
        output_path: Path,
        suu_mass: float,
        max_extra_jets: int,
        seed: int | None = None,
        delphes_card_path: Path | None = None,
        num_events: int = 100_000,
    ) -> None:
        super().__init__(output_path, suu_mass, seed, delphes_card_path, num_events)
        self.max_extra_jets = max_extra_jets

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        decays: list[str] = ["h > b b~", "h > v v, v > j j"]

        commands: list[MadGraphCommand] = (
            vector_boson_multiparticle_definition_commands()
        )

        commands += [
            CommentCommand("Generate Higgs background"),
            CommentCommand(""),
        ]

        index = 0

        for higgs_decay in decays:
            commands.append(CommentCommand(f"Processes with {higgs_decay} decay"))

            for num_extra_jets in range(0, self.max_extra_jets + 1):
                if num_extra_jets > 0:
                    extra_jets = " " + " ".join("j" * num_extra_jets)
                else:
                    extra_jets = ""

                process = f"p p > h{extra_jets}, ({higgs_decay})"
                subprocess_label = f"@{index}"

                if index == 0:
                    commands.append(GenerateProcessCommand(process, subprocess_label))
                else:
                    commands.append(AddProcessCommand(process, subprocess_label))

                index += 1

        return commands


@final
class SingleBosonBackgroundGenerator(BackgroundProcessCommandsGenerator):
    max_extra_jets: int

    def __init__(
        self,
        output_path: Path,
        suu_mass: float,
        max_extra_jets: int = 4,
        seed: int | None = None,
        delphes_card_path: Path | None = None,
        num_events: int = 100_000,
    ) -> None:
        super().__init__(output_path, suu_mass, seed, delphes_card_path, num_events)
        self.max_extra_jets = max_extra_jets

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        commands = vector_boson_multiparticle_definition_commands()

        commands += [
            CommentCommand("Generate v + jets background"),
            GenerateProcessCommand(
                "p p > v, v > j j",
                subprocess_label="@0",
            ),
        ]

        for num_extra_jets in range(1, self.max_extra_jets + 1):
            extra_jets = " ".join("j" * num_extra_jets)
            commands.append(
                AddProcessCommand(
                    f"p p > v {extra_jets}, v > j j",
                    subprocess_label=f"@{num_extra_jets}",
                )
            )

        return commands


@final
class SingleBosonPlusHiggsBackgroundGenerator(BackgroundProcessCommandsGenerator):
    max_extra_jets: int

    def __init__(
        self,
        output_path: Path,
        suu_mass: float,
        max_extra_jets: int,
        seed: int | None = None,
        delphes_card_path: Path | None = None,
        num_events: int = 100_000,
    ) -> None:
        super().__init__(output_path, suu_mass, seed, delphes_card_path, num_events)
        self.max_extra_jets = max_extra_jets

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        decays: list[str] = ["h > b b~", "h > v v, v > j j"]

        commands: list[MadGraphCommand] = (
            vector_boson_multiparticle_definition_commands()
        )

        commands += [
            CommentCommand("Generate Higgs + single boson background"),
            CommentCommand(""),
        ]

        index = 0

        for higgs_decay in decays:
            commands.append(CommentCommand(f"Processes with {higgs_decay} decay"))

            for num_extra_jets in range(0, self.max_extra_jets + 1):
                if num_extra_jets > 0:
                    extra_jets = " " + " ".join("j" * num_extra_jets)
                else:
                    extra_jets = ""

                process = f"p p > v h{extra_jets}, (v > j j), ({higgs_decay})"
                subprocess_label = f"@{index}"

                if index == 0:
                    commands.append(GenerateProcessCommand(process, subprocess_label))
                else:
                    commands.append(AddProcessCommand(process, subprocess_label))

                index += 1

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
        num_events: int = 100_000,
    ) -> None:
        super().__init__(output_path, suu_mass, seed, delphes_card_path, num_events)
        self.max_extra_jets = max_extra_jets

    @override
    def process_generation_commands(self) -> list[MadGraphCommand]:
        commands = vector_boson_multiparticle_definition_commands()

        commands += [
            CommentCommand("Generate dibosons background"),
            GenerateProcessCommand(
                "p p > v v, v > j j",
                subprocess_label="@0",
            ),
        ]

        for num_extra_jets in range(1, self.max_extra_jets + 1):
            extra_jets = " ".join("j" * num_extra_jets)
            commands.append(
                AddProcessCommand(
                    f"p p > v v {extra_jets}, v > j j",
                    subprocess_label=f"@{num_extra_jets}",
                )
            )

        return commands
