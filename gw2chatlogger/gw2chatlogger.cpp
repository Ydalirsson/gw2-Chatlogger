#include "gw2chatlogger.h"
#include <QFileDialog>
#include <QListWidgetItem>
#include <QDateTime>
#include <QDir>
#include <algorithm>
#include <vector>
#include <tesseract/baseapi.h>
#include <tesseract/ocrclass.h>
#include <leptonica/allheaders.h>
#include "optionsTab.h"


gw2chatlogger::gw2chatlogger(QWidget *parent)
    : QMainWindow(parent)
{
    ui.setupUi(this);

    auto* optionsTab = new OptionsTab(this);

    // Füge es dem TabWidget hinzu
    ui.tabWidget->addTab(optionsTab, "Options");

    connect(ui.selectImagesBtn, &QPushButton::clicked, this, [this]() {
        QStringList files = QFileDialog::getOpenFileNames(this, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp)");
        struct ImageInfo {
            QString path;
            QDateTime created;
        };
        std::vector<ImageInfo> images;
        for (const QString& file : files) {
            QFileInfo info(file);
            images.push_back({file, info.birthTime()});
        }
        std::sort(images.begin(), images.end(), [](const ImageInfo& a, const ImageInfo& b) {
            return a.created < b.created;
        });
        ui.imageListWidget->clear();
        for (const auto& img : images) {
            QListWidgetItem* item = new QListWidgetItem(img.path);
            item->setData(Qt::UserRole, img.created);
            ui.imageListWidget->addItem(item);
        }
    });

    connect(ui.startBatchOcrBtn, &QPushButton::clicked, this, [this]() {
        ui.ocrResultTextEdit->clear();
        for (int i = 0; i < ui.imageListWidget->count(); ++i) {
            QListWidgetItem* item = ui.imageListWidget->item(i);
            QString imagePath = item->text();
            QString ocrText = runTesseract(imagePath);
            ui.ocrResultTextEdit->append(QString("File: %1\n%2\n").arg(imagePath, ocrText));
        }
    });
}

QString gw2chatlogger::runTesseract(const QString& imagePath)
{
    tesseract::TessBaseAPI tess;
    if (tess.Init("./tessdata_fast", "deu")) { // Use "eng" for English, change as needed
        return "Tesseract init failed";
    }

    Pix* image = pixRead(imagePath.toStdString().c_str());
    if (!image) {
        return "Failed to read image";
    }

    tess.SetImage(image);
    char* outText = tess.GetUTF8Text();
    QString result = outText ? QString::fromUtf8(outText) : "OCR failed";

    // Clean up
    delete[] outText;
    pixDestroy(&image);
    tess.End();

    return result;
}

gw2chatlogger::~gw2chatlogger(){}

