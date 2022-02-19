#pragma once

#include <QtWidgets/QMainWindow>
#include <QFileDialog>
#include <QDateTime>
#include "ui_gw2chatlogger.h"

#include "logger.h"

using namespace std;

class GW2Chatlogger : public QMainWindow
{
    Q_OBJECT

public:
    GW2Chatlogger(QWidget *parent = Q_NULLPTR);
    ~GW2Chatlogger();

public slots:
    void startLogging();
    void stopLogging();
    void tryOutConvert();
    void selectChatBoxArea();
    void saveChatBoxArea();
    void saveSPM();
    void selectLanguages();
    void savePath();

private:
    Ui::GW2ChatloggerClass ui;
    Logger log;

    void updateUISettings();
};