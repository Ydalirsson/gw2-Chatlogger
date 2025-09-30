#include "gw2chatlogger.h"
#include <QtWidgets/QApplication>

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    gw2chatlogger window;
    window.show();
    return app.exec();
}
