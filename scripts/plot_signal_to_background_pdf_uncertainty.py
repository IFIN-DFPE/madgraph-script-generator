from argparse import ArgumentParser
from ctypes import c_double
from pathlib import Path

import numpy as np
import pandas as pd
import ROOT


def propagate_uncertainty_division(a, b, ratio, stddev_a, stddev_b):
    return np.sqrt((ratio**2) * ((stddev_a / a) ** 2 + (stddev_b / b) ** 2))


def main() -> None:
    parser = ArgumentParser("plot_signal_to_background_pdf_uncertainty.py")

    _ = parser.add_argument(
        "signal_csv_path",
        action="store",
        type=Path,
        default="signal_pdf_variation.csv",
    )

    _ = parser.add_argument(
        "background_csv_path",
        action="store",
        type=Path,
        default="background_pdf_variation.csv",
    )

    _ = parser.add_argument(
        "--output",
        action="store",
        type=Path,
        default="s_to_b_pdf_uncertainty.pdf",
        help="Output file path",
    )

    _ = parser.add_argument(
        "--width", action="store", type=int, default=1400, help="Width of canvas"
    )
    _ = parser.add_argument(
        "--height", action="store", type=int, default=800, help="Height of canvas"
    )

    args = parser.parse_args()

    width: int = args.width
    height: int = args.height

    # Read data
    signal_csv_file_path: Path = args.signal_csv_path
    background_csv_file_path: Path = args.background_csv_path

    signal_df = pd.read_csv(signal_csv_file_path)
    background_df = pd.read_csv(background_csv_file_path)

    num_pdfs = len(signal_df)

    signal_cross_section_fb: np.ndarray = 1000 * signal_df.cross_section_pb.to_numpy()
    background_cross_section_fb: np.ndarray = (
        1000 * background_df.cross_section_pb.to_numpy()
    )

    signal_pdf_variation_percentage_above: np.ndarray = (
        signal_df.pdf_variation_percentage_above.to_numpy()
    )
    signal_pdf_variation_percentage_below: np.ndarray = (
        signal_df.pdf_variation_percentage_below.to_numpy()
    )

    signal_pdf_stddev_above = (
        signal_cross_section_fb * signal_pdf_variation_percentage_above / 100.0
    )
    signal_pdf_stddev_below = (
        signal_cross_section_fb * signal_pdf_variation_percentage_below / 100.0
    )

    background_pdf_variation_percentage_above: np.ndarray = (
        background_df.pdf_variation_percentage_above.to_numpy()
    )
    background_pdf_variation_percentage_below: np.ndarray = (
        background_df.pdf_variation_percentage_below.to_numpy()
    )

    background_pdf_stddev_above = (
        background_cross_section_fb * background_pdf_variation_percentage_above / 100.0
    )
    background_pdf_stddev_below = (
        background_cross_section_fb * background_pdf_variation_percentage_below / 100.0
    )

    s_to_b_cross_section_ratio = signal_cross_section_fb / background_cross_section_fb

    # Propagation of uncertainty formula
    y_err_above = propagate_uncertainty_division(
        signal_cross_section_fb,
        background_cross_section_fb,
        s_to_b_cross_section_ratio,
        signal_pdf_stddev_above,
        background_pdf_stddev_above,
    )
    y_err_below = propagate_uncertainty_division(
        signal_cross_section_fb,
        background_cross_section_fb,
        s_to_b_cross_section_ratio,
        signal_pdf_stddev_below,
        background_pdf_stddev_below,
    )

    # Make plot
    canvas = ROOT.TCanvas("canvas", "PDF uncertainties", width, height)

    canvas.SetLeftMargin(0.14)
    canvas.SetGrid(0, 1)

    hr = canvas.DrawFrame(
        -1.5,
        s_to_b_cross_section_ratio.min() * 0.5,
        num_pdfs + 0.5,
        s_to_b_cross_section_ratio.max() * 1.4,
    )
    hr.SetTitle("Signal-to-background cross section ratio for various PDFs")
    hr.SetXTitle("Parton Distribution Function")
    hr.SetYTitle("Cross section ratio (adimensional)")
    hr.GetXaxis().CenterTitle()
    hr.GetYaxis().CenterTitle()
    hr.SetTickLength(0)
    hr.GetXaxis().SetLabelSize(0)

    graph = ROOT.TGraphAsymmErrors(
        num_pdfs,
        np.arange(num_pdfs, dtype=np.float64),
        s_to_b_cross_section_ratio,
        0,
        0,
        y_err_below,
        y_err_above,
    )

    graph.SetLineWidth(2)
    graph.SetMarkerColor(4)
    graph.SetMarkerStyle(20)
    graph.SetMarkerSize(1.5)

    graph.Draw("P")

    text = ROOT.TText()
    text.SetTextColorAlpha(ROOT.kBlue, 0.8)
    text.SetTextAlign(22)
    text.SetTextSize(0.025)
    # text.SetTextAngle(20)

    for i in range(graph.GetN()):
        x, y = c_double(), c_double()
        graph.GetPoint(i, x, y)
        x, y = x.value, y.value
        pdf_name: str = signal_df.pdf_name[i]
        pdf_name = pdf_name.split(",")[0].strip()
        text.DrawText(x, y + 0.0002, pdf_name)

    latex = ROOT.TLatex()
    latex.SetTextSize(0.025)
    latex.SetTextAlign(12)
    latex.DrawLatexNDC(0.18, 0.2, "MadGraph 3.5.15")

    output_path = args.output
    canvas.Print(str(output_path))


if __name__ == "__main__":
    main()
