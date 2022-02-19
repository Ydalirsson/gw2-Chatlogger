#include "gw2chatlogger.h"

GW2Chatlogger::GW2Chatlogger(QWidget *parent)
    : QMainWindow(parent)
{
    ui.setupUi(this);

	connect(ui.recordBtn, &QPushButton::pressed, this, &GW2Chatlogger::startLogging);
	connect(ui.StopBtn, &QPushButton::pressed, this, &GW2Chatlogger::stopLogging);
    connect(ui.TryBtn, &QPushButton::pressed, this, &GW2Chatlogger::tryOutConvert);
	connect(ui.SetAreaBtn, &QPushButton::pressed, this, &GW2Chatlogger::selectChatBoxArea);

	connect(ui.savePointsBtn, &QPushButton::pressed, this, &GW2Chatlogger::saveChatBoxArea);
	connect(ui.saveSpmBtn, &QPushButton::pressed, this, &GW2Chatlogger::saveSPM);
	//connect(ui.TryBtn, &QPushButton::pressed, this, &GW2Chatlogger::selectLanguages);
	connect(ui.changeSaveLocBtn, &QPushButton::pressed, this, &GW2Chatlogger::savePath);

	updateUISettings();
}

GW2Chatlogger::~GW2Chatlogger()
{
}

void GW2Chatlogger::startLogging()
{
	// TODO: log in right file -- input
	QString newChatLogFile = QString::fromStdString(log.config.getLogSavingLocation());
	newChatLogFile.append("\\test213.txt");
	QFile file(newChatLogFile);
	file.open(QFile::ReadWrite | QFile::Text);
	QTextStream stream(&file);
	stream << "dfgdfgdfg";
	file.close();

	//log.reset();
	//log.start();
}

void GW2Chatlogger::stopLogging()
{
	log.stop();
}

void GW2Chatlogger::tryOutConvert()
{
	Mat screen = log.singleShot();
	QString newString = log.convertPicToText(screen);
	ui.logBrowserLbl->setText(newString);
}

void GW2Chatlogger::selectChatBoxArea()
{
	string windowName = "Select text of chatbox";
	bool fromCenter = false;
	bool showCrosshair = true;
	
	ui.infoMsgLbl->setText(QString("Set a white rectangle. Confirm it with SPACE or ENTER. Press C to cancel this process."));

	Mat screen = log.fullscreenShot();
	Rect2d r = selectROI(windowName, screen, showCrosshair, fromCenter);
	
	cv::destroyAllWindows();
	string fullName = to_string(r.x) + " " + to_string(r.y)+ " " + to_string(r.width) + " " + to_string(r.height) + to_string(r.x + r.width) + " " + to_string(r.y + r.height);

	ui.infoMsgLbl->setText(QString::fromStdString(fullName));
	log.config.setArea(r.x, r.y, r.width, r.height);
	updateUISettings();
}

void GW2Chatlogger::saveChatBoxArea()
{
	log.config.setArea(ui.newX1Edit->value(), ui.newY1Edit->value(), ui.newX2Edit->value(), ui.newY2Edit->value());
	updateUISettings();
}

void GW2Chatlogger::saveSPM()
{
	log.config.setSPM(ui.newSpmEdit->value());
	updateUISettings();
}

// TODO: check signal and events to save
void GW2Chatlogger::selectLanguages()
{
	
	log.config.setLanguages(ui.engCheckBox->isChecked(), ui.gerCheckBox->isChecked(), ui.espCheckbox->isChecked(), ui.fraCheckBox->isChecked());
	updateUISettings();
}

void GW2Chatlogger::savePath()
{
	char const* userProfile = getenv("USERPROFILE");
	QString dir = QFileDialog::getExistingDirectory(this, tr("Open Directory"),
		userProfile, QFileDialog::ShowDirsOnly | QFileDialog::DontUseNativeDialog);
	log.config.setLogSavingLocation(dir.toStdString());
	updateUISettings();
}

void GW2Chatlogger::updateUISettings()
{
	this->ui.x1CurrentLbl->setText(QString::number(log.config.getAreaX1()));
	this->ui.y1CurrentLbl->setText(QString::number(log.config.getAreaY1()));
	this->ui.x2CurrentLbl->setText(QString::number(log.config.getAreaX2()));
	this->ui.y2CurrentLbl->setText(QString::number(log.config.getAreaY2()));
	this->ui.spmCurrentLbl->setText(QString::number(log.config.getSPM()));
	this->ui.logFileLocationCurrentLbl->setText(QString::fromStdString(log.config.getLogSavingLocation()));
}