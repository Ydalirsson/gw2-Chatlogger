#pragma once

#include <QDebug>
#include <QThread>

#include <tesseract/baseapi.h>
#include <leptonica/allheaders.h>

#include <Windows.h>
#include <opencv2/core.hpp>
#include <opencv2/opencv.hpp>
#include <opencv2/video/tracking.hpp>

#include <opencv2/imgproc.hpp>
#include <opencv2/highgui.hpp>

#include "configurator.h"

using namespace std;
using namespace cv;

class Logger : public QThread
{
    Q_OBJECT

public:
	Logger();
	~Logger();

    void run() Q_DECL_OVERRIDE;
    void stop();
    void reset();

    Mat fullscreenShot();
    Mat singleShot();
    QString convertPicToText(Mat);

    Configurator config;
   
private:
    bool haltFlag = false;

    BITMAPINFOHEADER createBitmapHeader(int width, int height);
    Mat captureScreenMat(HWND hwnd, unsigned int x1, unsigned int y1, unsigned int x2, unsigned int y2);
};