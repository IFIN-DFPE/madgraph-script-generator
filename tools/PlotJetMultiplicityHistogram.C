void PlotJetMultiplicityHistogram(TString input_filename, TString output_filename = "jet_multiplicity.pdf") {
    ROOT::EnableImplicitMT();

    auto file = TFile::Open(input_filename);

    auto df = new ROOT::RDataFrame("Delphes", file);

    auto hist = df->Histo1D({"jet_multiplicity", "Jet Multiplicity", 64, 0, 20}, "Jet_size");

    auto canvas = new TCanvas("canvas", "Jet Multiplicity", 800, 600);
    hist->SetLineColor(kBlue);
    hist->SetLineWidth(2);
    hist->Draw();
    canvas->SaveAs(output_filename);
}
