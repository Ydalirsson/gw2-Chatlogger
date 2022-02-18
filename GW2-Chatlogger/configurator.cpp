#include "configurator.h"

#include <QSettings>

Configurator::Configurator()
{
	this->settings.x1 = 0;
	this->settings.y1 = 0;
	this->settings.x2 = 0;
	this->settings.y2 = 0;
	this->settings.spm = 0;
	this->settings.checkedEN = true;
	this->settings.checkedDE = false;
	this->settings.checkedES = false;
	this->settings.checkedFR = false;

	char const* userProfile = getenv("USERPROFILE");
	if (userProfile == NULL) {
		return;
	}
	else {
		string saveLoc(userProfile);
		saveLoc.append("\\Documents\\Guild Wars 2\\Chatlogs\\");
		saveLoc.append(this->filename);
		this->settings.logSavingLocation = saveLoc;
	}
	
	// set default seetings
	QFile file(QString::fromStdString(this->settings.logSavingLocation));
	if (!file.exists())
	{
		configFile = new QSettings(QString::fromStdString(this->settings.logSavingLocation), QSettings::IniFormat);
		configFile->beginGroup("/saving_folder");
		configFile->setValue("path", QString::fromStdString(this->settings.logSavingLocation));
		configFile->endGroup();
		configFile->beginGroup("/recording");
		configFile->setValue("x1", this->settings.x1);
		configFile->setValue("y1", this->settings.y1);
		configFile->setValue("x2", this->settings.x2);
		configFile->setValue("y2", this->settings.y2);
		configFile->setValue("spm", this->settings.spm);
		configFile->endGroup();
		configFile->beginGroup("/languages");
		configFile->setValue("en", this->settings.checkedEN = true);
		configFile->setValue("de", this->settings.checkedDE = false);
		configFile->setValue("es", this->settings.checkedES = false);
		configFile->setValue("fr", this->settings.checkedFR = false);
		configFile->endGroup();
	} 
	// load data from file
	else
	{
		configFile = new QSettings(QString::fromStdString(this->settings.logSavingLocation), QSettings::IniFormat);
		configFile->beginGroup("/saving_folder");
		settings.logSavingLocation = configFile->value("path").toString().toLatin1().constData();
		configFile->endGroup();
		configFile->beginGroup("/recording");
		settings.x1 = configFile->value("x1").toInt();
		settings.y1 = configFile->value("y1").toInt();
		settings.x2 = configFile->value("x2").toInt();
		settings.y2 = configFile->value("y2").toInt();
		configFile->endGroup();
		configFile->beginGroup("/languages");
		settings.checkedEN = configFile->value("en").toBool();
		settings.checkedDE = configFile->value("de").toBool();
		settings.checkedES = configFile->value("es").toBool();
		settings.checkedFR = configFile->value("fr").toBool();
		configFile->endGroup();
	}
}

Configurator::~Configurator()
{

}

void Configurator::setLogSavingLocation(string saveLoc)
{
	this->settings.logSavingLocation = saveLoc;

	configFile = new QSettings(QString::fromStdString(this->settings.logSavingLocation), QSettings::IniFormat);
	configFile->beginGroup("/saving_folder");
	configFile->setValue("path", QString::fromStdString(this->settings.logSavingLocation));
	configFile->endGroup();
}

void Configurator::setLanguages(bool eng, bool ger, bool esp, bool fra)
{
	this->settings.checkedEN = eng;
	this->settings.checkedDE = ger;
	this->settings.checkedES = esp;
	this->settings.checkedFR = fra;

	configFile = new QSettings(QString::fromStdString(this->settings.logSavingLocation), QSettings::IniFormat);
	configFile->beginGroup("/languages");
	configFile->setValue("en", this->settings.checkedEN);
	configFile->setValue("de", this->settings.checkedDE);
	configFile->setValue("es", this->settings.checkedES);
	configFile->setValue("fr", this->settings.checkedFR);
	configFile->endGroup();
}

void Configurator::setArea(unsigned int x1, unsigned int y1, unsigned int x2, unsigned int y2)
{
	this->settings.x1 = x1;
	this->settings.y1 = y1;
	this->settings.x2 = x2;
	this->settings.y2 = y2;

	configFile = new QSettings(QString::fromStdString(this->settings.logSavingLocation), QSettings::IniFormat);
	configFile->beginGroup("/recording");
	configFile->setValue("x1", this->settings.x1);
	configFile->setValue("y1", this->settings.y1);
	configFile->setValue("x2", this->settings.x2);
	configFile->setValue("y2", this->settings.y2);
	configFile->endGroup();
}

void Configurator::setSPM(unsigned int spm)
{
	this->settings.spm = spm;

	configFile = new QSettings(QString::fromStdString(this->settings.logSavingLocation), QSettings::IniFormat);
	configFile->beginGroup("/recording");
	configFile->setValue("spm", this->settings.spm);
	configFile->endGroup();
}

t_settings Configurator::loadSettings()
{
	return this->settings;
}

string Configurator::getLogSavingLocation()
{
	return this->settings.logSavingLocation;
}

unsigned int Configurator::getAreaX1()
{
	return this->settings.x1;
}

unsigned int Configurator::getAreaY1()
{
	return this->settings.y1;
}

unsigned int Configurator::getAreaX2()
{
	return this->settings.x2;
}

unsigned int Configurator::getAreaY2()
{
	return this->settings.y2;
}

unsigned int Configurator::getSPM()
{
	return this->settings.spm;
}

unsigned int Configurator::getLanguages()
{
	// TODO: build lang string 
	return this->settings.checkedDE;
}