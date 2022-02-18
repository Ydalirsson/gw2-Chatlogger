#pragma once

#include <iostream>
#include <fstream>
#include <string>

#include <QFile>
#include <QSettings>

using namespace std;

struct t_settings {
	string logSavingLocation;	// [saving folders]
	unsigned int x1;			// [recording]
	unsigned int y1;
	unsigned int x2;
	unsigned int y2;
	unsigned int spm;			
	bool checkedEN;				// [languages]
	bool checkedDE;
	bool checkedES;
	bool checkedFR;
};   

class Configurator
{

public:
	Configurator();
	~Configurator();
	/*
	static Configurator& getInstance()
	{
		static Configurator instance;	// Guaranteed to be destroyed.				
		return instance;				// Instantiated on first use.
	}
	Configurator(Configurator const&) = delete;
	void operator=(Configurator const&) = delete;
	*/

	void setLogSavingLocation(string saveLoc);
	void setLanguages(bool eng, bool ger, bool esp, bool fra);
	void setArea(unsigned int x1, unsigned int y1, unsigned int x2, unsigned int y2);
	void setSPM(unsigned int spm);

	t_settings loadSettings();
	string getLogSavingLocation();
	unsigned int getLanguages();
	unsigned int getAreaX1();
	unsigned int getAreaY1();
	unsigned int getAreaX2();
	unsigned int getAreaY2();
	unsigned int getSPM();

private:
	QSettings* configFile = 0;
	t_settings settings;
	string filename = "settings.ini";
};