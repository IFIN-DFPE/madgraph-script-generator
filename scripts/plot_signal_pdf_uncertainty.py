from argparse import ArgumentParser
from ctypes import c_double
from pathlib import Path

import numpy as np
import pandas as pd
import ROOT


def main() -> None:
    parser = ArgumentParser("plot_signal_pdf_uncertainty.py")

    _ = parser.add_argument(
        "input_csv_path",
        action="store",
        type=Path,
        default="pdf_variation.csv",
    )

    _ = parser.add_argument(
        "--output",
        action="store",
        type=Path,
        default="Suu_pdf_uncertainty.pdf",
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
    csv_file_path: Path = args.input_csv_path

    df = pd.read_csv(csv_file_path)

    num_pdfs = len(df)

    # Make plot
    canvas = ROOT.TCanvas("canvas", "Suu -> Chi Chi cross sections", width, height)

    canvas.SetLeftMargin(0.14)
    canvas.SetGrid(0, 1)

    hr = canvas.DrawFrame(-1.5, 1e-3, num_pdfs + 0.5, 4e-3)
    hr.SetTitle("PDF impact on S_{uu} decay cross section")
    hr.SetXTitle("Parton Distribution Function")
    hr.SetYTitle("Cross section (fb)")
    hr.GetXaxis().CenterTitle()
    hr.GetYaxis().CenterTitle()
    hr.SetTickLength(0)
    hr.GetXaxis().SetLabelSize(0)

    cross_section_fb: np.ndarray = 1000 * df.cross_section_pb.to_numpy()
    pdf_variation_percentage_above: np.ndarray = (
        df.pdf_variation_percentage_above.to_numpy()
    )
    pdf_variation_percentage_below: np.ndarray = (
        df.pdf_variation_percentage_below.to_numpy()
    )
    y_err_above = cross_section_fb * pdf_variation_percentage_above / 100.0
    y_err_below = cross_section_fb * np.abs(pdf_variation_percentage_below) / 100.0

    graph = ROOT.TGraphAsymmErrors(
        num_pdfs,
        np.arange(num_pdfs, dtype=np.float64),
        cross_section_fb,
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
        pdf_name: str = df.pdf_name[i]
        pdf_name = pdf_name.split(",")[0].strip()
        text.DrawText(x, y + 0.0002, pdf_name)

    latex = ROOT.TLatex()
    latex.SetTextSize(0.025)
    latex.SetTextAlign(12)
    latex.DrawLatexNDC(0.18, 0.2, "MadGraph 3.5.15")
    latex.DrawLatexNDC(
        0.18, 0.16, "Suu #rightarrow #chi #chi #rightarrow W^{+}b h^{0} t"
    )

    output_path = args.output
    canvas.Print(str(output_path))


if __name__ == "__main__":
    main()
