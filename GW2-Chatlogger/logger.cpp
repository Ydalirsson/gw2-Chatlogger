#include "logger.h"

Logger::Logger()
{

}

Logger::~Logger()
{

}

void Logger::run()
{
    while (true) {
		if (haltFlag)
		{
			break;
		}
		else
		{
			if (checkActiveWindow())
			{
				Mat screen = singleShot();
				convertInfo logEntry = convertPicToText(screen);

				QString msgToWrite = removeAlreadyExistingMsg(logEntry.outString);

				if (!msgToWrite.isEmpty())
				{
					QFile chatLogFile(filename);
					chatLogFile.open(QIODevice::WriteOnly | QIODevice::Append);
					QTextStream stream(&chatLogFile);
					stream << msgToWrite << endl;
					chatLogFile.close();
				}
			}
			else
			{
				//  infoMsg.configure(text='GW2 is not the active and focused window')
			}
			Sleep(1.0/(config.getSPM()/60.0));
		}
    }
 }

void Logger::stop()
{
    this->haltFlag = true;
}

void Logger::reset()
{
    this->haltFlag = false;
}

void Logger::setFilename(QString chatLogFile)
{
	this->filename = chatLogFile;
}

QString Logger::getFilename()
{
	return this->filename;
}

bool Logger::checkActiveWindow()
{
	HWND foreground = GetForegroundWindow();
	if (foreground)
	{
		wchar_t window_title[256];
		GetWindowText(foreground, window_title, 256);
		wstring ws(window_title);
		string str(ws.begin(), ws.end());
		if (str == "Guild Wars 2")
		{
			qDebug() << "Window is active";
			return true;
		}
		else
		{
			qDebug() << "Window not active";
			return false;
		}
	}

	return false;
}

QString Logger::removeAlreadyExistingMsg(QString convertedText)
{
	QStringList screenLines = convertedText.split('\n');
	QStringList textFileLines;
	QStringList newMsgsLines;
	QString	msgToWrite;

	QFile file(filename);
	file.open(QFile::ReadOnly | QFile::Text);
	QTextStream in(&file);
	textFileLines = in.readAll().split('\n');
	file.close();
	
	for (auto word : textFileLines) {
		if (word.isEmpty()) textFileLines.removeAll(word);
	}
	for (auto word : screenLines) {
		if (word.isEmpty()) screenLines.removeAll(word);
	}
	for (auto msg : screenLines) {
		if (!textFileLines.contains(msg)) newMsgsLines.append(msg);
	}

	for (auto singleMsg : newMsgsLines) {
		msgToWrite = msgToWrite + singleMsg + '\n';
	}
//	if (msgToWrite.isEmpty()) return;

	return msgToWrite;
}

Mat Logger::fullscreenShot()
{
	HWND hwnd = GetDesktopWindow();
	Mat fullscreen = captureScreenMat(hwnd, 0, 0, GetSystemMetrics(SM_CXSCREEN), GetSystemMetrics(SM_CYSCREEN));

	cv::cvtColor(fullscreen, fullscreen, 6); // 6 - COLOR_BGR2GRAY

	return fullscreen;
}

Mat Logger::singleShot()
{
	HWND hwnd = GetDesktopWindow();
	Mat src = captureScreenMat(hwnd, config.getAreaX1(), config.getAreaY1(), config.getAreaX2(), config.getAreaY2());
	Mat resized_up;

	cv::resize(src, resized_up, Size(), 2.0, 2.0, INTER_CUBIC);
	src.release();
	//cv::blur(resized_up, resized_up, cv::Size(5, 5));
	//cv::cvtColor(resized_up, resized_up, 6); // 6 - COLOR_BGR2GRAY
	
	//cv::imshow("Bearbeitetes Bild", resized_up);

	return resized_up;
}

convertInfo Logger::convertPicToText(Mat pic)
{
	convertInfo convertInfo;
	convertInfo.usedLanguages = config.getLanguagesStr();
	char* outText;

	// Initialize tesseract-ocr with English, without specifying tessdata path
	tesseract::TessBaseAPI* api = new tesseract::TessBaseAPI();
	if (api->Init("tessdata", convertInfo.usedLanguages.c_str(), tesseract::OEM_LSTM_ONLY))
	{
		fprintf(stderr, "Could not initialize tesseract.\n");
		exit(1);
	}
	api->SetPageSegMode(tesseract::PSM_SINGLE_BLOCK);
	api->SetVariable("tessedit_char_blacklist", "|");
	api->SetVariable("user_defined_dpi", "300");
	api->SetImage((uchar*)pic.data, pic.size().width, pic.size().height, pic.channels(), pic.step1());
	clock_t t = clock();
	api->Recognize(0);
	
	// Get OCR result
	outText = api->GetUTF8Text();
	convertInfo.outString = QString::fromUtf8(outText);
	t = clock() - t;
	convertInfo.timeNeeded = ((double)t) / CLOCKS_PER_SEC; // in seconds

	// Destroy used object and release memory
	api->End();
	delete api;
	delete[] outText;

	pic.release();

	return convertInfo;
}

BITMAPINFOHEADER Logger::createBitmapHeader(int width, int height)
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

Mat Logger::captureScreenMat(HWND hwnd, unsigned int x1, unsigned int y1, unsigned int x2, unsigned int y2)
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