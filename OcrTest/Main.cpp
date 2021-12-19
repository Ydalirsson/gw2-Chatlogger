#include <tesseract/baseapi.h>
#include <leptonica/allheaders.h>
#include <chrono>
#include <iostream>
#include <vector>
#include <memory>
#include <algorithm>

using namespace std;

int main(void)
{
    tesseract::TessBaseAPI* api = new tesseract::TessBaseAPI();
    if (api->Init("D:\\VisualProjects\\OcrTest\\tessdata", "eng", tesseract::OEM_LSTM_ONLY)) {
        fprintf(stderr, "Could not initialize tesseract.\n");
        return 1;
    }
    api->SetPageSegMode(tesseract::PSM_SINGLE_BLOCK);

    Pix* image = pixRead("D:\\text.jpg");
    if (!image) {
        fprintf(stderr, "Leptonica can't process input file!\n");
        return 2;
    }
    api->SetImage(image);
    int page = 0;
    pixDestroy(&image);
    std::chrono::steady_clock::time_point begin = std::chrono::steady_clock::now();
    char* outText = api->GetUTF8Text();
    std::chrono::steady_clock::time_point end = std::chrono::steady_clock::now();
    printf("\n%s", outText);
    if (outText)
        delete[] outText;
    api->End();

    std::cout << "Time difference = " << std::chrono::duration_cast<std::chrono::milliseconds>(end - begin).count() << "[ms]" << std::endl;
    std::cout << "Time difference = " << std::chrono::duration_cast<std::chrono::milliseconds>(end - begin).count() / 1000.0 << "[s]" << std::endl;
    
    system("PAUSE");
    return 0;
}
