#include <sstream>
#include <iostream>
#include <string>
#include <vector>
#include "stdlib.h"
#include "TFile.h"
#include "TTree.h"
using namespace std;

const Int_t maxnh = 2000;
Int_t b_npg;
Int_t b_pid[maxnh];
Float_t b_ptg[maxnh], b_etag[maxnh], b_phig[maxnh];

int parseFileName(string dataFile);
void makeTree(string dataFile)
{
	int job = parseFileName(dataFile);

	//TFile * in = new TFile(Form("/store/user/palmerjh/Results/job-%d/particle_list.dat"))
	TFile out(Form("makeTree_%d.root", job), "RECREATE", "ROOT file with tree"); // output file 
	TTree *tree = new TTree("tree","Event tree with a few branches");
	tree->Branch("npg", &b_npg, "npg/I");   // # of particles in event
  	tree->Branch("ptg", &b_ptg, "ptg[npg]/F");  // transverse momentum of each particle;
  	tree->Branch("etag", &b_etag, "etag[npg]/F"); // eta for each particle
  	tree->Branch("phig", &b_phig, "phig[npg]/F"); // phi for each particle
  	tree->Branch("pid", &b_pid, "pid[npg]/I"); // pid for each particle; pid_lookup.dat in same directory as particle_list.dat

	ifstream infile(dataFile);
	//ifstream infile(Form("job-%d/particle_list.dat", job));
	string line;

	Int_t eventCounter = 0;

	if (!(getline(infile, line))) { exit(1); } // error

	do {
		istringstream nParticles(line);
		if (!(nParticles >> b_npg)) { exit(1); } // error

		if (!(getline(infile, line))) { exit(1); } // error
		istringstream pTArray(line);
		for (int i = 0; i < b_npg; i++) {
			if (!(pTArray >> b_ptg[i])) { exit(1); } // error
		}

		if (!(getline(infile, line))) { exit(1); } // error
		istringstream etaArray(line);
		for (int i = 0; i < b_npg; i++) {
			if (!(etaArray >> b_etag[i])) { exit(1); } // error
		}

		if (!(getline(infile, line))) { exit(1); } // error
		istringstream phiArray(line);
		for (int i = 0; i < b_npg; i++) {
			if (!(phiArray >> b_phig[i])) { exit(1); } // error
		}

		if (!(getline(infile, line))) { exit(1); } // error
		istringstream pidArray(line);
		for (int i = 0; i < b_npg; i++) {
			if (!(pidArray >> b_pid[i])) { exit(1); } // error
		}

		eventCounter++;
		if (eventCounter % 10 == 0) cout << Form("Processed %d events", eventCounter) << endl;

		tree->Fill();

	} while (getline(infile, line));
	
	cout << "Writing tree to file" << endl;
	tree->Write();
	out.Write();
	cout << "Closing file" << endl;
	out.Close();

	cout << "This is the end, my only friend." << endl;

	//delete tree;
	//tree = 0;

}

int parseFileName(string dataFile)
{
	bool slash = false;
	int indexLo = dataFile.length() - 1;
	int indexHi = -1;
	for (;indexLo >= 0; indexLo--) {
		char ch = dataFile.at(indexLo);
		if (ch == '/') {
			slash = true;
			indexHi = indexLo;
			continue;
		}
		if (slash && (ch == '-')) {
			indexLo++;
			break;
		}
	}

	string number = dataFile.substr(indexLo, indexHi - indexLo);
	int jobID;
	istringstream ( number ) >> jobID;

	return jobID;
}
