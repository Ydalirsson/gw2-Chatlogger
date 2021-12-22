#include "gw2chatlogger.h"

#include <tesseract/baseapi.h>
#include <leptonica/allheaders.h>

using namespace cv;

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

void GW2Chatlogger::selectChatBoxArea()
{
	HWND hwnd = GetDesktopWindow();
	Mat src = captureScreenMat(hwnd);


	bool showCrosshair = false;
	bool fromCenter = false;
	Rect2d r = selectROI("Image", src, fromCenter, showCrosshair);
}

BITMAPINFOHEADER createBitmapHeader(int width, int height)
{
	BITMAPINFOHEADER  bi;

	// create a bitmap
	bi.biSize = sizeof(BITMAPINFOHEADER);
	bi.biWidth = width;
	bi.biHeight = -height;  //this is the line that makes it draw upside down or not
	bi.biPlanes = 1;
	bi.biBitCount = 32;
	bi.biCompression = BI_RGB;
	bi.biSizeImage = 0;
	bi.biXPelsPerMeter = 0;
	bi.biYPelsPerMeter = 0;
	bi.biClrUsed = 0;
	bi.biClrImportant = 0;

	return bi;
}

/**
 * Capture a screen window as a matrix.
 *
 * @param hwnd : window handle.
 *
 * @return Mat (Mat of the captured image)
 */
Mat captureScreenMat(HWND hwnd)
{
	Mat src;

	// get handles to a device context (DC)
	HDC hwindowDC = GetDC(hwnd);
	HDC hwindowCompatibleDC = CreateCompatibleDC(hwindowDC);
	SetStretchBltMode(hwindowCompatibleDC, COLORONCOLOR);

	// define scale, height and width
	int scale = 1;
	int screenx = GetSystemMetrics(SM_XVIRTUALSCREEN);
	int screeny = GetSystemMetrics(SM_YVIRTUALSCREEN);
	int width = GetSystemMetrics(SM_CXVIRTUALSCREEN);
	int height = GetSystemMetrics(SM_CYVIRTUALSCREEN);

	// create mat object
	src.create(height, width, CV_8UC4);

	// create a bitmap
	HBITMAP hbwindow = CreateCompatibleBitmap(hwindowDC, width, height);
	BITMAPINFOHEADER bi = createBitmapHeader(width, height);

	// use the previously created device context with the bitmap
	SelectObject(hwindowCompatibleDC, hbwindow);

	// copy from the window device context to the bitmap device context
	StretchBlt(hwindowCompatibleDC, 0, 0, width, height, hwindowDC, screenx, screeny, width, height, SRCCOPY);  //change SRCCOPY to NOTSRCCOPY for wacky colors !
	GetDIBits(hwindowCompatibleDC, hbwindow, 0, height, src.data, (BITMAPINFO*)&bi, DIB_RGB_COLORS);            //copy from hwindowCompatibleDC to hbwindow

	// avoid memory leak
	DeleteObject(hbwindow);
	DeleteDC(hwindowCompatibleDC);
	ReleaseDC(hwnd, hwindowDC);

	return src;
}