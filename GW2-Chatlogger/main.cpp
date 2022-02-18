#include "gw2chatlogger.h"
#include <QtWidgets/QApplication>

#include <iostream>

using namespace cv;
using namespace std;

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
    GW2Chatlogger w;

    w.show();
    return a.exec();
}