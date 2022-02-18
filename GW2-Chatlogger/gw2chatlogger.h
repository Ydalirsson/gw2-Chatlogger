#pragma once

#include <QtWidgets/QMainWindow>
#include <QTimer>
#include "ui_gw2chatlogger.h"

#include <tesseract/baseapi.h>
#include <leptonica/allheaders.h>

#include <Windows.h>
#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>
#include <opencv2/video/tracking.hpp>

#include <opencv2/imgproc.hpp>
#include <opencv2/highgui.hpp>

#include <time.h>

#include "configurator.h"
#include "logger.h"

using namespace std;
using namespace cv;

class GW2Chatlogger : public QMainWindow
{
    Q_OBJECT

public:
    GW2Chatlogger(QWidget *parent = Q_NULLPTR);
    ~GW2Chatlogger();

public slots:
    void startLogging();
    void stopLogging();
    void display();
    void selectChatBoxArea();
    void loggingData();

private:
    Ui::GW2ChatloggerClass ui;
    Configurator config;
    QTimer* timer;
    Logger log;

    BITMAPINFOHEADER createBitmapHeader(int width, int height);
    Mat captureScreenMat(HWND hwnd, unsigned int x1, unsigned int y1, unsigned int x2, unsigned int y2);
    void updateUISettings();
};