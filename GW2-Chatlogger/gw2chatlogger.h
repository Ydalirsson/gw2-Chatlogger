#pragma once

#include <QtWidgets/QMainWindow>
#include "ui_gw2chatlogger.h"

#include <Windows.h>
#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>
#include <opencv2/video/tracking.hpp>

class GW2Chatlogger : public QMainWindow
{
    Q_OBJECT

public:
    GW2Chatlogger(QWidget *parent = Q_NULLPTR);
    ~GW2Chatlogger();

public slots:
    void display();
    void selectChatBoxArea();

private:
    Ui::GW2ChatloggerClass ui;

   // BITMAPINFOHEADER createBitmapHeader(int width, int height);
    // Mat captureScreenMat(HWND hwnd);
};
