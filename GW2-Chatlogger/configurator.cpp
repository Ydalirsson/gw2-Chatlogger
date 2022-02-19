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
		defaultPath = userProfile;
		defaultPath.append("\\Documents\\Guild Wars 2\\Chatlogs\\settings.ini");
	}
	
	// set default seetings
	QFile file(QString::fromStdString(defaultPath));
	if (!file.exists())
	{
		configFile = new QSettings(QString::fromStdString(defaultPath), QSettings::IniFormat);
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
		configFile->beginGroup("/saving_folder");
		configFile->setValue("path", QString::fromStdString(this->settings.logSavingLocation));
		configFile->endGroup();
	} 
	// load data from file
	else
	{
		configFile = new QSettings(QString::fromStdString(defaultPath), QSettings::IniFormat);
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
		configFile->beginGroup("/saving_folder");
		settings.logSavingLocation = configFile->value("path").toString().toLatin1().constData();
		configFile->endGroup();
	}
}

Configurator::~Configurator()
{

}

void Configurator::setArea(unsigned int x1, unsigned int y1, unsigned int x2, unsigned int y2)
{
	this->settings.x1 = x1;
	this->settings.y1 = y1;
	this->settings.x2 = x2;
	this->settings.y2 = y2;

	configFile = new QSettings(QString::fromStdString(defaultPath), QSettings::IniFormat);
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

	configFile = new QSettings(QString::fromStdString(defaultPath), QSettings::IniFormat);
	configFile->beginGroup("/recording");
	configFile->setValue("spm", this->settings.spm);
	configFile->endGroup();
}

void Configurator::setLanguages(bool eng, bool ger, bool esp, bool fra)
{
	this->settings.checkedEN = eng;
	this->settings.checkedDE = ger;
	this->settings.checkedES = esp;
	this->settings.checkedFR = fra;

	configFile = new QSettings(QString::fromStdString(defaultPath), QSettings::IniFormat);
	configFile->beginGroup("/languages");
	configFile->setValue("en", this->settings.checkedEN);
	configFile->setValue("de", this->settings.checkedDE);
	configFile->setValue("es", this->settings.checkedES);
	configFile->setValue("fr", this->settings.checkedFR);
	configFile->endGroup();
}

void Configurator::setLogSavingLocation(string saveLoc)
{
	this->settings.logSavingLocation = saveLoc;

	configFile = new QSettings(QString::fromStdString(defaultPath), QSettings::IniFormat);
	configFile->beginGroup("/saving_folder");
	configFile->setValue("path", QString::fromStdString(this->settings.logSavingLocation));
	configFile->endGroup();
}

t_settings Configurator::loadSettings()
{
	return this->settings;
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

Qt::CheckState Configurator::getLanguagesCheckState(unsigned int nmbLang)
{
	unsigned int langChecked[4] = { this->settings.checkedEN, this->settings.checkedDE, this->settings.checkedES, this->settings.checkedFR };
	if (langChecked[nmbLang]) { return Qt::CheckState::Checked; }
	else { return Qt::CheckState::Unchecked; }
}

string Configurator::getLanguagesStr()
{
	// TODO: build lang string 
	unsigned int langChecked[4] = { this->settings.checkedEN, this->settings.checkedDE, this->settings.checkedES, this->settings.checkedFR };
	unsigned int langCounter = this->settings.checkedEN + this->settings.checkedDE + this->settings.checkedES + this->settings.checkedFR;
	string activatedLanguages = "eng";

	if (langCounter == 0)
	{
		return "eng";
	}
	else if (langCounter == 1)
	{
		if (langChecked[0] == 1) { return "eng";}
		if (langChecked[1] == 1) { return "deu"; }
		if (langChecked[2] == 1) { return "spa"; }
		if (langChecked[3] == 1) { return "fra"; }
	}
	else if (langCounter > 1)
	{
		activatedLanguages = "";

		if (langChecked[0] == 1) { activatedLanguages.append("eng+"); }
		if (langChecked[1] == 1) { activatedLanguages.append("deu+"); }
		if (langChecked[2] == 1) { activatedLanguages.append("spa+"); }
		if (langChecked[3] == 1) { activatedLanguages.append("fra+"); }

		activatedLanguages = activatedLanguages.substr(0, activatedLanguages.size() - 1);
		return activatedLanguages;
	}

	return activatedLanguages;
}

string Configurator::getLogSavingLocation()
{
	return this->settings.logSavingLocation;
}
