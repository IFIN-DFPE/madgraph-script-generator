# MadGraph5_aMC@NLO script generator

## Description

[MadGraph](http://madgraph.phys.ucl.ac.be/) is a popular suite of tools for generating [Feynman diagrams](https://en.wikipedia.org/wiki/Feynman_diagram) for a given particle interaction process, computing matrix elements and performing [Monte Carlo simulations](https://en.wikipedia.org/wiki/Monte_Carlo_method). Together with the [MadEvent](https://arxiv.org/abs/hep-ph/0208156) event generator / phase space sampler, the [Pythia](https://pythia.org/) showering/hadronization routines and [Delphes](https://delphes.github.io/) for detector simulation, they form a complete toolkit for numerical simulations of collider physics phenomenology.

Besides the interactive user interface, MadGraph also supports reading and executing commands from an input file. Unfortunately, the declarative syntax of this file format is very limited, making it hard to automate or streamline certain generation workflows.

The **MadGraph script generator** (this project) introduces a [Python](https://www.python.org/) interface for generating MG script files, allowing users who need more customizability to generate MG commands using their own code.

## Usage

The toolkit is designed to be imported and used in short Python scripts, which then generate the required MadGraph scripts. See the [`diquark-simulations`](https://github.com/IFIN-DFPE/diquark-simulations) repo for examples.

After the script files have been generated and saved to disk, we also offer an utility script, `scripts/run_scripts.py`, which can help run the scripts sequentially on the local computer. It's best to run it through [`nohup`](https://en.wikipedia.org/wiki/Nohup):

```shell
nohup python3 scripts/run_scripts.py path/to/generated/scripts/directory &
```

It can also submit the scripts as [SLURM](https://slurm.schedmd.com/overview.html) jobs.
