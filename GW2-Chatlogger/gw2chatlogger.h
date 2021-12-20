#pragma once

#include <QtWidgets/QMainWindow>
#include "ui_gw2chatlogger.h"

class GW2Chatlogger : public QMainWindow
{
    Q_OBJECT

public:
    GW2Chatlogger(QWidget *parent = Q_NULLPTR);
    ~GW2Chatlogger();

public slots:
    void display();

private:
    Ui::GW2ChatloggerClass ui;
};
