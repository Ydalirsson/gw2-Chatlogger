#include "gw2chatlogger.h"

#include <tesseract/baseapi.h>
#include <leptonica/allheaders.h>

GW2Chatlogger::GW2Chatlogger(QWidget *parent)
    : QMainWindow(parent)
{
    ui.setupUi(this);

    connect(ui.TryBtn, &QPushButton::pressed, this, &GW2Chatlogger::display);
}

GW2Chatlogger::~GW2Chatlogger()
{
}

void GW2Chatlogger::display()
{
    char* outText;

    tesseract::TessBaseAPI* api = new tesseract::TessBaseAPI();
    // Initialize tesseract-ocr with English, without specifying tessdata path
    if (api->Init("D:\\VisualProjects\\gw2-Chatlogger\\tessdata", "eng")) {
        fprintf(stderr, "Could not initialize tesseract.\n");
        exit(1);
    }

    // Open input image with leptonica library
    Pix* image = pixRead("D:\\text.jpg");
    api->SetImage(image);
    // Get OCR result
    outText = api->GetUTF8Text();
    //printf("OCR output:\n%s", outText);
    ui.logBrowserLbl->setText(QString::fromUtf8(outText));

    // Destroy used object and release memory
    api->End();
    delete api;
    delete[] outText;
    pixDestroy(&image);
}