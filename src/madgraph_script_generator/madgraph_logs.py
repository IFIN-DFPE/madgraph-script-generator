"Tools for working with and extracting data from MadGraph log files."

import re

NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN: str = (
    r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+\-]?\d+)?"
)
"""
Pattern for matching real numbers writing using scientific/exponential (E) notation.

Taken from https://stackoverflow.com/a/658662/5723188
"""

MADGRAPH_RESULTS_SUMMARY_PATTERN: re.Pattern[str] = re.compile(
    rf"""=== Results Summary for run: ((?:\w|\.)+) tag: ((?:\w|\.)+) ===
\s*Cross-section : \s*({NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN})\s*\+-\s* ({NUMBER_IN_SCIENTIFIC_NOTATION_PATTERN}) pb
\s*Nb of events :  (\d+)""",
    re.MULTILINE,
)
"""
Regular expression for matching run summaries
(with capture groups for run names, tags and cross-sections).
"""
