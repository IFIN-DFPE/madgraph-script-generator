"""This generation script uses the MG script generation toolkit
to reproduce the main results of the paper https://arxiv.org/abs/2503.17031.
"""

from pathlib import Path
from typing import Annotated

import typer

from madgraph_script_generator.commands import (
    CommentCommand,
    ComputeWidthsCommand,
    DoneCommand,
    GenerateProcessCommand,
    ImportModelCommand,
    LaunchCommand,
    MadGraphCommand,
    OutputCommand,
    SetCommand,
    SetExternalToolsCommand,
    convert_commands_to_str,
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
        ImportModelCommand("sm"),
    ]

    return commands


def phase_space_cuts_commands(suu_mass: float) -> list[MadGraphCommand]:
    return [
        CommentCommand("=== Phase space cuts ==="),
        SetCommand("dsqrt_shat", f"{(suu_mass - 0.5) * 1000:.0f}"),
    ]


def common_generation_commands(
    suu_mass: float, seed: int = 17
) -> list[MadGraphCommand]:
    commands: list[MadGraphCommand] = []

    commands += [
        SetExternalToolsCommand(
            analysis="MadAnalysis5", shower="Pythia", detector="Delphes"
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
        CommentCommand(
            "ME-PS boundary is at 30GeV, boundary between ME and PS (should be 20-100 GeV at LHC)"
        ),
        SetCommand("xqcut", "30.0"),
    ]

    commands += phase_space_cuts_commands(suu_mass)

    commands += [
        CommentCommand("Fix the seed for reproducibility"),
        SetCommand("iseed", str(seed), card="run_card"),
    ]

    return commands


def generate_signal_wb_wb_commands(
    diquark_model_path: Path, output_path: Path, suu_mass: float
) -> list[MadGraphCommand]:
    commands = common_initial_commands()

    commands += [
        CommentCommand("Import BSM diquark model"),
        ImportModelCommand(diquark_model_path),
    ]

    commands += [
        CommentCommand("Main process"),
        GenerateProcessCommand(
            " p p > suu, (suu > chi chi, (chi > w+ b, w+ > j j), (chi > w+ b, w+ > j j))"
        ),
    ]

    commands += [
        CommentCommand("Configure output directory"),
        OutputCommand(output_path),
    ]

    commands.append(LaunchCommand())

    commands += common_generation_commands(suu_mass)

    commands += [
        CommentCommand("Generate a reasonable number of events"),
        SetCommand("nevents", "30000"),
    ]

    commands += [
        CommentCommand(f"Mass of S_{{uu}} = {suu_mass} TeV"),
        SetCommand("MSuu", f"{suu_mass * 1000:.0f}"),
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


def generate_background_ttbar_commands(
    output_path: Path, extra_jets: int, suu_mass: float
) -> list[MadGraphCommand]:
    commands = common_initial_commands()

    extra_jets_str = ""
    if extra_jets > 0:
        extra_jets_str = " " + " ".join("j" * extra_jets)

    commands += [
        CommentCommand("Generate t tbar background"),
        GenerateProcessCommand(f"p p > t t~{extra_jets_str}", "QED=0"),
    ]

    commands += [
        CommentCommand("Configure output directory"),
        OutputCommand(output_path),
    ]

    commands.append(LaunchCommand())

    commands += common_generation_commands(suu_mass)

    commands += [
        CommentCommand("Generate a sufficient number of background events"),
        SetCommand("nevents", "50000"),
    ]

    return commands


def generate_background_qcd_commands(
    output_path: Path, final_state_jets: int, suu_mass: float
) -> list[MadGraphCommand]:
    assert final_state_jets > 0, (
        "At least one final state jet is required for the QCD multijet background"
    )

    commands = common_initial_commands()

    jets_str = " ".join("j" * final_state_jets)

    commands += [
        CommentCommand("Generate QCD multijet background"),
        GenerateProcessCommand(f"p p > {jets_str}", "QED=0"),
    ]

    commands += [
        CommentCommand("Configure output directory"),
        OutputCommand(output_path),
    ]

    commands.append(LaunchCommand())

    commands += common_generation_commands(suu_mass)

    return commands


def main(
    diquark_model_path: Path = Path(
        # pyright: ignore[reportCallInDefaultInitializer]
        "/data/iduminic/MG5_aMC_v3_5_12/models/diquarkVquark2023_UFO/"
    ),
    scripts_output_directory: Annotated[Path, typer.Argument()] = Path(
        # pyright: ignore[reportCallInDefaultInitializer]
        "diquark-repro/scripts"
    ),
    madgraph_output_directory: Annotated[Path, typer.Argument()] = Path(
        # pyright: ignore[reportCallInDefaultInitializer]
        "diquark-repro/data"
    ),
    debug: Annotated[
        bool,
        typer.Option(
            help="Print generated commands to stdout before saving them to file"
        ),
    ] = False,
) -> None:
    scripts_output_directory = scripts_output_directory.resolve()
    madgraph_output_directory = madgraph_output_directory.resolve()

    # For now, we generate scripts only for a single possible mass of the diquark scalar
    suu_mass = 8.0  # TeV

    print("Generating MadGraph command script for signal process...")

    signal_name = f"Suu_chichi_WbWb_MSuu_{suu_mass:.1g}TeV"

    wb_wb_signal_commands = generate_signal_wb_wb_commands(
        diquark_model_path, madgraph_output_directory / "signal" / signal_name, suu_mass
    )

    if debug:
        print(f"=== Commands for signal {signal_name} ===")
        print(convert_commands_to_str(wb_wb_signal_commands))
        print()

    signal_script_path = scripts_output_directory / "signal" / f"{signal_name}.txt"
    signal_script_path.parent.mkdir(parents=True, exist_ok=True)

    write_commands_to_file(
        signal_script_path,
        wb_wb_signal_commands,
    )

    print("Generating MadGraph command scripts for background processes...")

    background_scripts_output_path = scripts_output_directory / "background"
    backgrounds_output_path = madgraph_output_directory / "background"

    # QCD multijet

    bkg_qcd_scripts_output_path = background_scripts_output_path / "qcd_multijet"
    bkg_qcd_scripts_output_path.mkdir(parents=True, exist_ok=True)

    for final_state_jets in range(1, 5):
        background_name = f"qcd_multijet_{final_state_jets}_jets"

        qcd_multijet_commands = generate_background_qcd_commands(
            backgrounds_output_path / background_name,
            final_state_jets,
            suu_mass,
        )

        if debug:
            print(
                f"=== Commands for QCD multijet with {final_state_jets} jets background ==="
            )
            print(convert_commands_to_str(qcd_multijet_commands))
            print()

        write_commands_to_file(
            bkg_qcd_scripts_output_path / f"{background_name}.txt",
            qcd_multijet_commands,
        )

    # t tbar + jets

    bkg_ttbar_scripts_output_path = background_scripts_output_path / "ttbar_plus_jets"
    bkg_ttbar_scripts_output_path.mkdir(parents=True, exist_ok=True)

    for extra_jets in range(0, 3):
        background_name = f"ttbar_plus_{extra_jets}_jets"

        ttbar_plus_jets_commands = generate_background_ttbar_commands(
            backgrounds_output_path / background_name,
            extra_jets,
            suu_mass,
        )

        if debug:
            print(f"=== Commands for ttbar + {extra_jets} jets background ===")
            print(convert_commands_to_str(ttbar_plus_jets_commands))
            print()

        write_commands_to_file(
            bkg_ttbar_scripts_output_path / f"{background_name}.txt",
            ttbar_plus_jets_commands,
        )


if __name__ == "__main__":
    typer.run(main)
