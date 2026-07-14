from argparse import ArgumentParser
from pathlib import Path

import numpy as np
import pandas as pd
import ROOT


def main() -> None:
    parser = ArgumentParser("plot_signal_cross_sections.py")

    parser.add_argument(
        "Wb_Wb_cross_sections_csv_path",
        action="store",
        type=Path,
        default="Suu_ChiChi_WbWb_cross_sections.csv",
    )

    parser.add_argument(
        "Wb_ht_cross_sections_csv_path",
        action="store",
        type=Path,
        default="Suu_ChiChi_Wbht_cross_sections.csv",
    )

    parser.add_argument(
        "--output",
        action="store",
        type=Path,
        default="Suu_mass_scan.pdf",
        help="Output file path",
    )

    parser.add_argument(
        "--width", action="store", type=int, default=800, help="Width of canvas"
    )
    parser.add_argument(
        "--height", action="store", type=int, default=600, help="Height of canvas"
    )

    args = parser.parse_args()

    width: int = args.width
    height: int = args.height

    canvas = ROOT.TCanvas("canvas", "Suu -> Chi Chi cross sections", width, height)

    canvas.SetLeftMargin(0.12)
    canvas.SetGrid()

    hr = canvas.DrawFrame(6, 0, 9, 5e-2)
    hr.SetTitle("S_{uu} decay channels cross sections")
    hr.SetXTitle("S_{uu} mass (TeV)")
    hr.SetYTitle("Cross section (fb)")
    canvas.GetFrame().SetBorderSize(12)

    wb_wb_file_path: Path = args.Wb_Wb_cross_sections_csv_path
    wb_ht_file_path: Path = args.Wb_ht_cross_sections_csv_path

    df_wb_wb = pd.read_csv(wb_wb_file_path)
    df_wb_ht = pd.read_csv(wb_ht_file_path)

    num_masses = len(df_wb_wb)

    graph1 = ROOT.TGraph(
        num_masses,
        df_wb_wb.suu_mass.to_numpy(),
        1000 * df_wb_wb.cross_section_pb.to_numpy(),
    )

    graph1.SetLineWidth(2)
    graph1.SetMarkerColor(4)
    graph1.SetMarkerStyle(20)
    graph1.SetMarkerSize(2)

    graph1.Draw("LP")

    graph2 = ROOT.TGraph(
        num_masses,
        df_wb_ht.suu_mass.to_numpy(),
        1000 * df_wb_ht.cross_section_pb.to_numpy(),
    )

    graph2.SetLineWidth(2)
    graph2.SetMarkerColor(9)
    graph2.SetMarkerStyle(21)
    graph2.SetMarkerSize(2)

    graph2.Draw("LP")

    legend = ROOT.TLegend(0.5, 0.6, 0.9, 0.9)
    legend.SetHeader("Processes", "C")
    legend.SetFillColor(ROOT.kWhite)
    legend.SetBorderSize(1)
    legend.SetTextSize(0.04)
    legend.AddEntry(graph1, "\\chi \\chi #rightarrow W^{+}b W^{+}b", "lp")
    legend.AddEntry(graph2, "\\chi \\chi #rightarrow W^{+}b h^{0}t", "lp")
    legend.Draw()

    latex = ROOT.TLatex()
    latex.SetTextSize(0.025)
    latex.SetTextAlign(12)
    latex.DrawLatexNDC(0.15, 0.2, "MadGraph 3.5.15")
    latex.DrawLatexNDC(0.15, 0.16, "NNPDF 4.0 LO, #alpha_{s} = 0.118")

    output_path = args.output
    canvas.Print(str(output_path))


if __name__ == "__main__":
    main()
