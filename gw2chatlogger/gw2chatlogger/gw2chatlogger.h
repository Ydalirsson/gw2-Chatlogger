#pragma once

#include <QtWidgets/QMainWindow>
#include "ui_gw2chatlogger.h"

class gw2chatlogger : public QMainWindow
{
    Q_OBJECT

public:
    gw2chatlogger(QWidget *parent = nullptr);
    ~gw2chatlogger();

private:
    Ui::gw2chatloggerClass ui;
};

