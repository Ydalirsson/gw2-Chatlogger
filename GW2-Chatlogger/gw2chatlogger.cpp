#include "gw2chatlogger.h"

GW2Chatlogger::GW2Chatlogger(QWidget *parent)
    : QMainWindow(parent)
{
    ui.setupUi(this);

	connect(ui.recordBtn, &QPushButton::pressed, this, &GW2Chatlogger::startLogging);
	connect(ui.StopBtn, &QPushButton::pressed, this, &GW2Chatlogger::stopLogging);
    connect(ui.TryBtn, &QPushButton::pressed, this, &GW2Chatlogger::display);
	connect(ui.SetAreaBtn, &QPushButton::pressed, this, &GW2Chatlogger::selectChatBoxArea);

	updateUISettings();
}

GW2Chatlogger::~GW2Chatlogger()
{
}

void GW2Chatlogger::startLogging()
{
	log.reset();
	log.start();
}

void GW2Chatlogger::stopLogging()
{
	log.stop();
}

void GW2Chatlogger::display()
{
	clock_t t;

	char* outText;
	tesseract::TessBaseAPI* api = new tesseract::TessBaseAPI();

	HWND hwnd = GetDesktopWindow();
	Mat src = captureScreenMat(hwnd, this->config.getAreaX1(), this->config.getAreaY1(), this->config.getAreaX2(), this->config.getAreaY2());
	Mat resized_up;

	cv::resize(src, resized_up, Size(), 2.0, 2.0, INTER_CUBIC);
	src.release();
	cv::blur(resized_up, resized_up, cv::Size(5, 5));
	cv::cvtColor(resized_up, resized_up, 6); // 6 - COLOR_BGR2GRAY

	// Initialize tesseract-ocr with English, without specifying tessdata path
	if (api->Init("D:\\VisualProjects\\gw2-Chatlogger\\tessdata", "eng+deu", tesseract::OEM_LSTM_ONLY))
	{
		fprintf(stderr, "Could not initialize tesseract.\n");
		exit(1);
	}
	api->SetPageSegMode(tesseract::PSM_SINGLE_BLOCK);
	api->SetVariable("tessedit_char_blacklist", "|");
	api->SetImage((uchar*)resized_up.data, resized_up.size().width, resized_up.size().height, resized_up.channels(), resized_up.step1());
	t = clock();
	api->Recognize(0);
	t = clock() - t;

	// Get OCR result
	outText = api->GetUTF8Text();

	ui.logBrowserLbl->setText(QString::fromUtf8(outText));
	/*imshow("image", resized_up);
	waitKey();

	cv::destroyWindow("image"); */
	// Destroy used object and release memory
	api->End();
	delete api;
	delete[] outText;
	
	resized_up.release();

	double time_taken = ((double)t) / CLOCKS_PER_SEC; // in seconds
	ui.infoMsgLbl->setText(QString::number(time_taken));
}

void GW2Chatlogger::selectChatBoxArea()
{
	bool fromCenter = false;
	bool showCrosshair = true;
	
	ui.infoMsgLbl->setText(QString("Set a white rectangle. Confirm it with SPACE or ENTER. Press C to cancel this process."));
	HWND hwnd = GetDesktopWindow();
	Mat src = captureScreenMat(hwnd, 0, 0, GetSystemMetrics(SM_CXSCREEN), GetSystemMetrics(SM_CYSCREEN));
	Rect2d r = selectROI("Select text of chatbox", src, showCrosshair, fromCenter);
	string fullName = to_string(r.x) + " " + to_string(r.y)+ " " + to_string(r.width) + " " + to_string(r.height) + to_string(r.x + r.width) + " " + to_string(r.y + r.height);
	// TODO: close automatically Window
	ui.infoMsgLbl->setText(QString::fromStdString(fullName));
	config.setArea(r.x, r.y, r.width, r.height);
	updateUISettings();
}

void GW2Chatlogger::loggingData()
{
	clock_t t;

	char* outText;
	tesseract::TessBaseAPI* api = new tesseract::TessBaseAPI();

	HWND hwnd = GetDesktopWindow();
	Mat src = captureScreenMat(hwnd, this->config.getAreaX1(), this->config.getAreaY1(), this->config.getAreaX2(), this->config.getAreaY2());
	Mat resized_up;

	cv::resize(src, resized_up, Size(), 2.0, 2.0, INTER_CUBIC);
	src.release();
	cv::blur(resized_up, resized_up, cv::Size(5, 5));
	cv::cvtColor(resized_up, resized_up, 6); // 6 - COLOR_BGR2GRAY

	// Initialize tesseract-ocr with English, without specifying tessdata path
	if (api->Init("D:\\VisualProjects\\gw2-Chatlogger\\tessdata", "eng+deu", tesseract::OEM_LSTM_ONLY))
	{
		fprintf(stderr, "Could not initialize tesseract.\n");
		exit(1);
	}
	api->SetPageSegMode(tesseract::PSM_SINGLE_BLOCK);
	api->SetVariable("tessedit_char_blacklist", "|");
	api->SetImage((uchar*)resized_up.data, resized_up.size().width, resized_up.size().height, resized_up.channels(), resized_up.step1());
	t = clock();
	api->Recognize(0);
	t = clock() - t;

	// Get OCR result
	outText = api->GetUTF8Text();

	//ui.logBrowserLbl->setText(QString::fromUtf8(outText));
	/*imshow("image", resized_up);
	waitKey();

	cv::destroyWindow("image"); */
	// Destroy used object and release memory
	api->End();
	delete api;
	delete[] outText;

	resized_up.release();

	double time_taken = ((double)t) / CLOCKS_PER_SEC; // in seconds
	ui.infoMsgLbl->setText(QString::number(time_taken));
}


BITMAPINFOHEADER GW2Chatlogger::createBitmapHeader(int width, int height)
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

Mat GW2Chatlogger::captureScreenMat(HWND hwnd, unsigned int x1, unsigned int y1, unsigned int x2, unsigned int y2)
{
	Mat src;

	// get handles to a device context (DC)
	HDC hwindowDC = GetDC(hwnd);
	HDC hwindowCompatibleDC = CreateCompatibleDC(hwindowDC);
	SetStretchBltMode(hwindowCompatibleDC, COLORONCOLOR);

	// define scale, height and width
	int scale = 1;
	int screenx = x1;
	int screeny = y1;
	int width = x2;
	int height = y2;

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

void GW2Chatlogger::updateUISettings()
{
	this->ui.x1CurrentLbl->setText(QString::number(config.getAreaX1()));
	this->ui.y1CurrentLbl->setText(QString::number(config.getAreaY1()));
	this->ui.x2CurrentLbl->setText(QString::number(config.getAreaX2()));
	this->ui.y2CurrentLbl->setText(QString::number(config.getAreaY2()));
	this->ui.spmCurrentLbl->setText(QString::number(config.getSPM()));
	/*this->ui.engCheckBox = ;
	this->ui.gerCheckBox = ;
	this->ui.espCheckbox = ;
	this->ui.fraCheckBox = ; */
	this->ui.logFileLocationCurrentLbl->setText(QString::fromStdString(config.getLogSavingLocation()));
}