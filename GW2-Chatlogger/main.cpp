#include "gw2chatlogger.h"
#include <QtWidgets/QApplication>

#include <opencv2/core.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>

using namespace cv;
using namespace std;

int main(int argc, char *argv[])
{
	/*
	Mat image = Mat::zeros(300, 600, CV_8UC3);
	circle(image, Point(250, 150), 100, Scalar(0, 255, 128), -100);
	circle(image, Point(350, 150), 100, Scalar(255, 255, 255), -100);
	imshow("Display Window", image);
	waitKey(0);
	*/

    QApplication a(argc, argv);
    GW2Chatlogger w;
    w.show();
    return a.exec();
}