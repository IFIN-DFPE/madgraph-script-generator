from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path
from textwrap import TextWrapper
from typing import TextIO, final
from typing_extensions import override


class MadGraphCommand(ABC):
    @abstractmethod
    def to_command_str(self) -> str:
        """Converts this command object to its string representation,
        which MadGraph can understand.
        """


_comments_wrapper = TextWrapper(initial_indent="# ", subsequent_indent="# ")


@final
class CommentCommand(MadGraphCommand):
    "Comment line. Ignored by MadGraph, but useful for documenting the generated file."

    content: str

    def __init__(self, content: str) -> None:
        self.content = content

    @override
    def to_command_str(self) -> str:
        return _comments_wrapper.fill(self.content.strip())


@final
class DoneCommand(MadGraphCommand):
    "Command for marking the end of a section of commands, or the end of the script."

    @override
    def to_command_str(self) -> str:
        return "done"


@final
class SetCommand(MadGraphCommand):
    "Command for setting a value within the run card or within some parameter card."

    def __init__(self, variable_name: str, value: str, card: str | None = None) -> None:
        self.variable = variable_name
        self.value = value
        self.card = card

    @override
    def to_command_str(self) -> str:
        return f"set {self.card + ' ' if self.card else ''}{self.variable} = {self.value}".strip()


@final
class DefineCommand(MadGraphCommand):
    "Command for defining new particle aliases."

    def __init__(self, label: str, members: str) -> None:
        self.label = label
        self.members = members

    @override
    def to_command_str(self) -> str:
        return f"define {self.label} = {self.members}".strip()


@final
class ImportModelCommand(MadGraphCommand):
    """Command for importing a model of particle physics, in UFO format.

    This is usually some variation of the Standard Model, or a Beyond Standard Model.
    """

    model: str | Path
    restriction: str | None
    options: str | None

    def __init__(
        self,
        model_name_or_path: str | Path,
        restriction: str | None = None,
        options: str | None = None,
    ):
        self.model = model_name_or_path
        self.restriction = restriction
        self.options = options

    @override
    def to_command_str(self) -> str:
        return f"import model {self.model}{self.restriction or ''} {self.options or ''}".strip()


class ProcessDefinitionCommand(MadGraphCommand, ABC):
    "Common abstract base class for the `generate / add process` commands."

    process: str
    orders: str | None
    subprocess_label: str | None

    def __init__(
        self,
        process: str,
        orders: str | None = None,
        subprocess_label: str | None = None,
    ) -> None:
        self.process = process.strip()
        self.orders = orders.strip() if orders else None

        if subprocess_label:
            subprocess_label = subprocess_label.strip()
            assert subprocess_label.startswith("@"), (
                "Subprocess label should start with an ampersand character"
            )

        self.subprocess_label = subprocess_label

    @staticmethod
    @abstractmethod
    def command_name() -> str: ...

    @override
    def to_command_str(self) -> str:
        return f"{self.command_name()} {self.process} {f'{self.orders} ' if self.orders else ''}{self.subprocess_label or ''}".strip()


@final
class GenerateProcessCommand(ProcessDefinitionCommand):
    """Command for telling MadGraph for which interaction (process)
    to generate diagrams (subprocesses).
    """

    @override
    @staticmethod
    def command_name() -> str:
        return "generate"


@final
class AddProcessCommand(ProcessDefinitionCommand):
    """Command for including additional processes in generation run."""

    @override
    @staticmethod
    def command_name() -> str:
        return "add process"


@final
class OutputCommand(MadGraphCommand):
    """Tells MadGraph where to save the generated process files,
    Feynman diagrams and event generator sources.
    """

    path: Path

    def __init__(self, output_path: Path) -> None:
        self.path = output_path

    @override
    def to_command_str(self) -> str:
        return f"output {self.path}".strip()


@final
class LaunchCommand(MadGraphCommand):
    """Instructs MadGraph to launch a new event generation run, possibly with a custom name,
    using the currently configured model and process(es).

    Configured tools and run/param cards can be customized before the run actually starts.
    """

    run_name: str | None
    "Name of the run to launch."

    def __init__(self, run_name: str | None = None) -> None:
        self.run_name = run_name

    @override
    def to_command_str(self) -> str:
        return f"launch {self.run_name or ''}".strip()


@final
class SetExternalToolsCommand(MadGraphCommand):
    "Command for configuring which external tools to use during the run."

    madspin: bool | None
    analysis: str | None
    shower: str | None
    detector: str | None

    def __init__(
        self,
        madspin: bool | None = None,
        analysis: str | None = None,
        shower: str | None = None,
        detector: str | None = None,
    ) -> None:
        self.madspin = madspin
        self.analysis = analysis
        self.shower = shower
        self.detector = detector

    @override
    def to_command_str(self) -> str:
        tool_settings: list[str] = []

        if self.madspin is not None:
            tool_settings.append(f"madspin={'ON' if self.madspin else 'OFF'}")

        if self.analysis is not None:
            tool_settings.append(f"analysis={self.analysis}".strip())

        if self.shower is not None:
            tool_settings.append(f"shower={self.shower}".strip())

        if self.detector is not None:
            tool_settings.append(f"detector={self.detector}".strip())

        return "\n".join(tool_settings)


@final
class DelphesCardCommand(MadGraphCommand):
    "Command for telling MadGraph to use a specific Delphes card for detector simulation."

    card_path: Path

    def __init__(self, card_path: Path) -> None:
        self.card_path = card_path

    @override
    def to_command_str(self) -> str:
        return str(self.card_path)


class ComputeWidthsCommand(MadGraphCommand):
    "Command for telling MadGraph to compute the widths of the given particles."

    particle_ids: list[int]

    def __init__(self, particle_ids: list[int]) -> None:
        self.particle_ids = particle_ids

    @override
    def to_command_str(self) -> str:
        particle_ids_str = " ".join(str(pid) for pid in self.particle_ids)
        return f"compute_widths {particle_ids_str}".strip()


def convert_commands_to_str(commands: Iterable[MadGraphCommand]) -> str:
    """Converts an iterable of MadGraph command objects
    into a single string representation of the generated script.
    """

    lines = [
        "# This file was generated automatically by MadGraph script generator.",
        "# Do not edit manually! Changes will be overwritten.",
        "",
    ]

    for command in commands:
        lines.append(command.to_command_str())
        if not isinstance(command, CommentCommand):
            lines.append("")

    return "\n".join(lines)


def write_commands_to_stream(
    stream: TextIO, commands: Iterable[MadGraphCommand]
) -> None:
    """Write the given iterable of MadGraph commands to an I/O stream."""

    commands_str = convert_commands_to_str(commands)
    written_count = stream.write(commands_str)

    if len(commands_str) != written_count:
        raise Exception(
            "Couldn't fully write generated MadGraph script to the given IO stream"
        )


def write_commands_to_file(path: Path, commands: Iterable[MadGraphCommand]) -> None:
    """Save the given iterable of MadGraph commands to a script file.

    Any existing file will be overwritten.
    """

    with open(path, "w") as file:
        write_commands_to_stream(file, commands)
