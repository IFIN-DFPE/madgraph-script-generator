from madgraph_script_generator.commands import DoneCommand


def test_done_command() -> None:
    command = DoneCommand()
    assert command.to_command_str() == "done"
