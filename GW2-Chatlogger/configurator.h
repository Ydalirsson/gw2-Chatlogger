#pragma once

#include <iostream>
#include <fstream>
#include <string>

#include <QFile>
#include <QSettings>

using namespace std;

struct t_settings {
	unsigned int x1;			// [recording]
	unsigned int y1;
	unsigned int x2;
	unsigned int y2;
	unsigned int spm;			
	bool checkedEN;				// [languages]
	bool checkedDE;
	bool checkedES;
	bool checkedFR;
	string logSavingLocation;	// [saving folders]
};   

class Configurator
{

public:
	Configurator();
	~Configurator();

	void setArea(unsigned int x1, unsigned int y1, unsigned int x2, unsigned int y2);
	void setSPM(unsigned int spm);
	void setLanguages(bool eng, bool ger, bool esp, bool fra);
	void setLogSavingLocation(string saveLoc);

	t_settings loadSettings();
	unsigned int getAreaX1();
	unsigned int getAreaY1();
	unsigned int getAreaX2();
	unsigned int getAreaY2();
	unsigned int getSPM();
	unsigned int getLanguages();
	string getLogSavingLocation();

private:
	QSettings* configFile = 0;
	t_settings settings;
	string defaultPath;
};