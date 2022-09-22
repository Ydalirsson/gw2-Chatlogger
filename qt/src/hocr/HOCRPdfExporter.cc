/* -*- Mode: C++; indent-tabs-mode: t; c-basic-offset: 4; tab-width: 4 -*-  */
/*
 * HOCRPdfExporter.cc
 * Copyright (C) 2013-2022 Sandro Mani <manisandro@gmail.com>
 *
 * gImageReader is free software: you can redistribute it and/or modify it
 * under the terms of the GNU General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * gImageReader is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
 * See the GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

#include "ConfigSettings.hh"
#include "Displayer.hh"
#include "common.hh"
#include "CCITTFax4Encoder.hh"
#include "HOCRPdfExporter.hh"
#include "HOCRPdfExportWidget.hh"
#include "HOCRDocument.hh"
#include "MainWindow.hh"
#include "PaperSize.hh"
#include "SourceManager.hh"
#include "Utils.hh"

#include <cstring>
#include <podofo/base/PdfDictionary.h>
#include <podofo/base/PdfFilter.h>
#include <podofo/base/PdfStream.h>
#include <podofo/doc/PdfFont.h>
#include <podofo/doc/PdfIdentityEncoding.h>
#include <podofo/doc/PdfImage.h>
#include <podofo/doc/PdfPage.h>
#include <podofo/doc/PdfPainter.h>
#include <podofo/doc/PdfStreamedDocument.h>
#include <QBuffer>
#include <QDesktopServices>
#include <QPainter>
#include <QThread>
#include <QUrl>


bool HOCRPdfExporter::run(const HOCRDocument* hocrdocument, const QString& outname, const ExporterSettings* settings) {
	const PDFSettings* pdfSettings = static_cast<const PDFSettings*>(settings);

	int pageCount = hocrdocument->pageCount();
	QString errMsg;
	MainWindow::ProgressMonitor monitor(pageCount);
	MAIN->showProgress(&monitor);

	double pageWidth, pageHeight;
	// Page dimensions are in points: 1 in = 72 pt
	if(pdfSettings->paperSize == "custom") {
		pageWidth = pdfSettings->paperWidthIn * 72.0;
		pageHeight = pdfSettings->paperHeightIn * 72.0;
	} else if (pdfSettings->paperSize != "source") {
		auto inchSize = PaperSize::getSize(PaperSize::inch, pdfSettings->paperSize.toStdString(), pdfSettings->paperSizeLandscape);
		pageWidth = inchSize.width * 72.0;
		pageHeight = inchSize.height * 72.0;
	}

	QFont defaultFont(pdfSettings->fallbackFontFamily, pdfSettings->fallbackFontSize);

	HOCRPdfPrinter* painter = nullptr;
	if(pdfSettings->backend == PDFSettings::BackendPoDoFo) {
		painter = HOCRPoDoFoPdfPrinter::create(outname, *pdfSettings, defaultFont, errMsg);
	} else if(pdfSettings->backend == PDFSettings::BackendQPrinter) {
		painter = new HOCRQPrinterPdfPrinter(outname, pdfSettings->creator, defaultFont);
	}

	bool success = Utils::busyTask([&] {
		for(int i = 0; i < pageCount; ++i) {
			if(monitor.cancelled()) {
				errMsg = _("The operation was cancelled");
				return false;
			}
			const HOCRPage* page = hocrdocument->page(i);
			if(page->isEnabled()) {
				QRect bbox = page->bbox();
				QString sourceFile = page->sourceFile();
				// If the source file is an image, its "resolution" is actually just the scale factor that was used for recognizing.
				bool isImage = !sourceFile.endsWith(".pdf", Qt::CaseInsensitive) && !sourceFile.endsWith(".djvu", Qt::CaseInsensitive);
				int sourceDpi = page->resolution();
				int sourceScale = sourceDpi;
				if(isImage) {
					sourceDpi *= pdfSettings->assumedImageDpi / 100;
				}
				// [pt] = 72 * [in]
				// [in] = 1 / dpi * [px]
				// => [pt] = 72 / dpi * [px]
				double px2pt = (72.0 / sourceDpi);
				double imgScale = double(pdfSettings->outputDpi) / sourceDpi;
				bool success = false;
				if(isImage) {
					QMetaObject::invokeMethod(this, "setSource", Qt::BlockingQueuedConnection, Q_RETURN_ARG(bool, success), Q_ARG(QString, sourceFile), Q_ARG(int, page->pageNr()), Q_ARG(int, int(sourceScale * imgScale)), Q_ARG(double, page->angle()));
				} else {
					QMetaObject::invokeMethod(this, "setSource", Qt::BlockingQueuedConnection, Q_RETURN_ARG(bool, success), Q_ARG(QString, sourceFile), Q_ARG(int, page->pageNr()), Q_ARG(int, pdfSettings->outputDpi), Q_ARG(double, page->angle()));
				}
				if(success) {
					if(pdfSettings->paperSize == "source") {
						pageWidth = bbox.width() * px2pt;
						pageHeight = bbox.height() * px2pt;
					}
					double offsetX = 0.5 * (pageWidth - bbox.width() * px2pt);
					double offsetY = 0.5 * (pageHeight - bbox.height() * px2pt);
					if(!painter->createPage(pageWidth, pageHeight, offsetX, offsetY, errMsg)) {
						return false;
					}
					painter->printChildren(page, *pdfSettings, px2pt, imgScale, double(sourceScale) / sourceDpi);
					if(pdfSettings->overlay) {
						QRect scaledRect(imgScale * bbox.left(), imgScale * bbox.top(), imgScale * bbox.width(), imgScale * bbox.height());
						QRect printRect(bbox.left() * px2pt, bbox.top() * px2pt, bbox.width() * px2pt, bbox.height() * px2pt);
						QImage selection;
						QMetaObject::invokeMethod(painter, "getSelection",  Qt::BlockingQueuedConnection, Q_RETURN_ARG(QImage, selection), Q_ARG(QRect, scaledRect));
						painter->drawImage(printRect, selection, *pdfSettings);
					}
					QMetaObject::invokeMethod(this, "setSource", Qt::BlockingQueuedConnection, Q_RETURN_ARG(bool, success), Q_ARG(QString, page->sourceFile()), Q_ARG(int, page->pageNr()), Q_ARG(int, sourceScale), Q_ARG(double, page->angle()));
					painter->finishPage();
				} else {
					errMsg = _("Failed to render page %1").arg(page->title());
					return false;
				}
			}
			monitor.increaseProgress();
		}
		return painter->finishDocument(errMsg);
	}, _("Exporting to PDF..."));
	delete painter;
	MAIN->hideProgress();
	if(!success) {
		QMessageBox::warning(MAIN, _("Export failed"), _("The PDF export failed: %1.").arg(errMsg));
	} else {
		bool openAfterExport = ConfigSettings::get<SwitchSetting>("openafterexport")->getValue();
		if(openAfterExport) {
			QDesktopServices::openUrl(QUrl::fromLocalFile(outname));
		}
	}
	return success;
}

bool HOCRPdfExporter::setSource(const QString& sourceFile, int page, int dpi, double angle) {
	if(MAIN->getSourceManager()->addSource(sourceFile, true)) {
		MAIN->getDisplayer()->setup(&page, &dpi, &angle);
		return true;
	} else {
		return false;
	}
}


void HOCRPdfPrinter::printChildren(const HOCRItem* item, const HOCRPdfExporter::PDFSettings& pdfSettings, double px2pu/*pixels to printer units*/, double imgScale, double fontScale) {
	if(!item->isEnabled()) {
		return;
	}
	if(pdfSettings.fontSize != -1) {
		setFontSize(pdfSettings.fontSize * fontScale);
	}
	QString itemClass = item->itemClass();
	QRect itemRect = item->bbox();
	int childCount = item->children().size();
	if(itemClass == "ocr_par" && pdfSettings.uniformizeLineSpacing) {
		double yInc = double(itemRect.height()) / childCount;
		double y = itemRect.top() + yInc;
		QPair<double, double> baseline = childCount > 0 ? item->children()[0]->baseLine() : qMakePair(0.0, 0.0);
		for(int iLine = 0; iLine < childCount; ++iLine, y += yInc) {
			HOCRItem* lineItem = item->children()[iLine];
			int x = itemRect.x();
			int prevWordRight = itemRect.x();
			for(int iWord = 0, nWords = lineItem->children().size(); iWord < nWords; ++iWord) {
				HOCRItem* wordItem = lineItem->children()[iWord];
				if(!wordItem->isEnabled()) {
					continue;
				}
				QRect wordRect = wordItem->bbox();
				setFontFamily(pdfSettings.fontFamily.isEmpty() ? wordItem->fontFamily() : pdfSettings.fontFamily, wordItem->fontBold(), wordItem->fontItalic());
				if(pdfSettings.fontSize == -1) {
					setFontSize(wordItem->fontSize() * pdfSettings.detectedFontScaling * fontScale);
				}
				// If distance from previous word is large, keep the space
				if(wordRect.x() - prevWordRight > pdfSettings.preserveSpaceWidth * getAverageCharWidth() / px2pu) {
					x = wordRect.x();
				}
				prevWordRight = wordRect.right();
				QString text = wordItem->text();
				if(iWord == nWords - 1 && pdfSettings.sanitizeHyphens) {
					text.replace(QRegularExpression("[-\u2014]\\s*$"), "-");
				}
				double wordBaseline = (x - itemRect.x()) * baseline.first + baseline.second;
				drawText(x * px2pu, (y + wordBaseline) * px2pu, text);
				x += getTextWidth(text + " ") / px2pu;
			}
		}
	} else if(itemClass == "ocr_line" && !pdfSettings.uniformizeLineSpacing) {
		QPair<double, double> baseline = item->baseLine();
		for(int iWord = 0, nWords = item->children().size(); iWord < nWords; ++iWord) {
			HOCRItem* wordItem = item->children()[iWord];
			if(!wordItem->isEnabled()) {
				continue;
			}
			QRect wordRect = wordItem->bbox();
			setFontFamily(pdfSettings.fontFamily.isEmpty() ? wordItem->fontFamily() : pdfSettings.fontFamily, wordItem->fontBold(), wordItem->fontItalic());
			if(pdfSettings.fontSize == -1) {
				setFontSize(wordItem->fontSize() * pdfSettings.detectedFontScaling * fontScale);
			}
			double y = itemRect.bottom() + (wordRect.center().x() - itemRect.x()) * baseline.first + baseline.second;
			QString text = wordItem->text();
			if(iWord == nWords - 1 && pdfSettings.sanitizeHyphens) {
				text.replace(QRegularExpression("[-\u2014]\\s*$"), "-");
			}
			drawText(wordRect.x() * px2pu, y * px2pu, text);
		}
	} else if(itemClass == "ocr_graphic" && !pdfSettings.overlay) {
		QRect scaledItemRect(itemRect.left() * imgScale, itemRect.top() * imgScale, itemRect.width() * imgScale, itemRect.height() * imgScale);
		QRect printRect(itemRect.left() * px2pu, itemRect.top() * px2pu, itemRect.width() * px2pu, itemRect.height() * px2pu);
		QImage selection;
		QMetaObject::invokeMethod(this, "getSelection", QThread::currentThread() == qApp->thread() ? Qt::DirectConnection : Qt::BlockingQueuedConnection, Q_RETURN_ARG(QImage, selection), Q_ARG(QRect, scaledItemRect));
		drawImage(printRect, selection, pdfSettings);
	} else {
		for(int i = 0, n = item->children().size(); i < n; ++i) {
			printChildren(item->children()[i], pdfSettings, px2pu, imgScale, fontScale);
		}
	}
}

QImage HOCRPdfPrinter::getSelection(const QRect& bbox) {
	Displayer* displayer = MAIN->getDisplayer();
	return displayer->getImage(bbox.translated(displayer->getSceneBoundingRect().toRect().topLeft()));
}


HOCRQPainterPdfPrinter::HOCRQPainterPdfPrinter(QPainter* painter, const QFont& defaultFont)
	: m_painter(painter), m_defaultFont(defaultFont) {
	m_curFont = m_defaultFont;
}

void HOCRQPainterPdfPrinter::setFontFamily(const QString& family, bool bold, bool italic) {
	float curSize = m_curFont.pointSize();
	if(m_fontDatabase.hasFamily(family)) {
		m_curFont.setFamily(family);
	}  else {
		m_curFont = m_defaultFont;
	}
	m_curFont.setPointSize(curSize);
	m_curFont.setBold(bold);
	m_curFont.setItalic(italic);
	m_painter->setFont(m_curFont);
}

void HOCRQPainterPdfPrinter::setFontSize(double pointSize) {
	if(pointSize != m_curFont.pointSize()) {
		m_curFont.setPointSize(pointSize);
		m_painter->setFont(m_curFont);
	}
}

void HOCRQPainterPdfPrinter::drawText(double x, double y, const QString& text) {
	m_painter->drawText(m_offsetX + x, m_offsetY + y, text);
}

void HOCRQPainterPdfPrinter::drawImage(const QRect& bbox, const QImage& image, const HOCRPdfExporter::PDFSettings& settings) {
	QImage img = convertedImage(image, settings.colorFormat, settings.conversionFlags);
	if(settings.compression == HOCRPdfExporter::PDFSettings::CompressJpeg) {
		QByteArray data;
		QBuffer buffer(&data);
		img.save(&buffer, "jpg", settings.compressionQuality);
		img = QImage::fromData(data);
	}
	m_painter->drawImage(bbox, img);
}

double HOCRQPainterPdfPrinter::getAverageCharWidth() const {
	return m_painter->fontMetrics().averageCharWidth();
}

double HOCRQPainterPdfPrinter::getTextWidth(const QString& text) const {
	return m_painter->fontMetrics().horizontalAdvance(text);
}


HOCRQPrinterPdfPrinter::HOCRQPrinterPdfPrinter(const QString& filename, const QString& creator, const QFont& defaultFont)
	: HOCRQPainterPdfPrinter(nullptr, defaultFont) {
	m_printer.setOutputFormat(QPrinter::PdfFormat);
	m_printer.setOutputFileName(filename);
	m_printer.setResolution(72); // This to ensure that painter units are points - images are passed pre-scaled to drawImage, so that the resulting dpi in the box is the output dpi (the document resolution only matters for images)
	m_printer.setFontEmbeddingEnabled(true);
	m_printer.setFullPage(true);
	m_printer.setCreator(creator);
}

HOCRQPrinterPdfPrinter::~HOCRQPrinterPdfPrinter() {
	delete m_painter;
}

bool HOCRQPrinterPdfPrinter::createPage(double width, double height, double offsetX, double offsetY, QString& errMsg) {
	m_printer.setPageSize(QPageSize(QSizeF(width, height), QPageSize::Point));
	if(!m_firstPage) {
		if(!m_printer.newPage()) {
			return false;
		}
	} else {
		// Need to create painter after setting paper size, otherwise default paper size is used for first page...
		m_painter = new QPainter();
		m_painter->setRenderHint(QPainter::Antialiasing);
		if(!m_painter->begin(&m_printer)) {
			errMsg = _("Failed to write to file");
			return false;
		}
		m_firstPage = false;
	}
	m_curFont = m_defaultFont;
	m_painter->setFont(m_curFont);
	m_offsetX = offsetX;
	m_offsetY = offsetY;
	return true;
}

bool HOCRQPrinterPdfPrinter::finishDocument(QString& /*errMsg*/) {
	return m_painter->end();
}

void HOCRQPrinterPdfPrinter::drawImage(const QRect& bbox, const QImage& image, const HOCRPdfExporter::PDFSettings& settings) {
	QImage img = convertedImage(image, settings.colorFormat, settings.conversionFlags);
	m_painter->drawImage(bbox, img);
}


#if PODOFO_VERSION < PODOFO_MAKE_VERSION(0,9,3)
namespace PoDoFo {
class PdfImageCompat : public PoDoFo::PdfImage {
	using PdfImage::PdfImage;
public:
	void SetImageDataRaw( unsigned int nWidth, unsigned int nHeight,
	                      unsigned int nBitsPerComponent, PdfInputStream* pStream ) {
		m_rRect.SetWidth( nWidth );
		m_rRect.SetHeight( nHeight );

		this->GetObject()->GetDictionary().AddKey( "Width",  PdfVariant( static_cast<pdf_int64>(nWidth) ) );
		this->GetObject()->GetDictionary().AddKey( "Height", PdfVariant( static_cast<pdf_int64>(nHeight) ) );
		this->GetObject()->GetDictionary().AddKey( "BitsPerComponent", PdfVariant( static_cast<pdf_int64>(nBitsPerComponent) ) );

		PdfVariant var;
		m_rRect.ToVariant( var );
		this->GetObject()->GetDictionary().AddKey( "BBox", var );

		this->GetObject()->GetStream()->SetRawData( pStream, -1 );
	}
};
}
#endif


HOCRPoDoFoPdfPrinter* HOCRPoDoFoPdfPrinter::create(const QString& filename, const HOCRPdfExporter::PDFSettings& settings, const QFont& defaultFont, QString& errMsg) {
	PoDoFo::PdfStreamedDocument* document = nullptr;
	PoDoFo::PdfFont* defaultPdfFont = nullptr;
#if PODOFO_VERSION >= PODOFO_MAKE_VERSION(0,9,3)
	const PoDoFo::PdfEncoding* pdfFontEncoding = PoDoFo::PdfEncodingFactory::GlobalIdentityEncodingInstance();
#else
	PoDoFo::PdfEncoding* pdfFontEncoding = new PoDoFo::PdfIdentityEncoding;
#endif

	try {
		const std::string password = settings.password.toStdString();
		PoDoFo::PdfEncrypt* encrypt = nullptr;
		if(!password.empty()) {
			encrypt = PoDoFo::PdfEncrypt::CreatePdfEncrypt(password,
			          password,
			          PoDoFo::PdfEncrypt::EPdfPermissions::ePdfPermissions_Print |
			          PoDoFo::PdfEncrypt::EPdfPermissions::ePdfPermissions_Edit |
			          PoDoFo::PdfEncrypt::EPdfPermissions::ePdfPermissions_Copy |
			          PoDoFo::PdfEncrypt::EPdfPermissions::ePdfPermissions_EditNotes |
			          PoDoFo::PdfEncrypt::EPdfPermissions::ePdfPermissions_FillAndSign |
			          PoDoFo::PdfEncrypt::EPdfPermissions::ePdfPermissions_Accessible |
			          PoDoFo::PdfEncrypt::EPdfPermissions::ePdfPermissions_DocAssembly |
			          PoDoFo::PdfEncrypt::EPdfPermissions::ePdfPermissions_HighPrint,
			          PoDoFo::PdfEncrypt::EPdfEncryptAlgorithm::ePdfEncryptAlgorithm_RC4V2);
		}
		PoDoFo::EPdfVersion pdfVersion = PoDoFo::ePdfVersion_Default;
		switch(settings.version) {
		case HOCRPdfExporter::PDFSettings::Version::PdfVersion_1_0:
			pdfVersion = PoDoFo::EPdfVersion::ePdfVersion_1_0;
			break;
		case HOCRPdfExporter::PDFSettings::Version::PdfVersion_1_1:
			pdfVersion = PoDoFo::EPdfVersion::ePdfVersion_1_1;
			break;
		case HOCRPdfExporter::PDFSettings::Version::PdfVersion_1_2:
			pdfVersion = PoDoFo::EPdfVersion::ePdfVersion_1_2;
			break;
		case HOCRPdfExporter::PDFSettings::Version::PdfVersion_1_3:
			pdfVersion = PoDoFo::EPdfVersion::ePdfVersion_1_3;
			break;
		case HOCRPdfExporter::PDFSettings::Version::PdfVersion_1_4:
			pdfVersion = PoDoFo::EPdfVersion::ePdfVersion_1_4;
			break;
		case HOCRPdfExporter::PDFSettings::Version::PdfVersion_1_5:
			pdfVersion = PoDoFo::EPdfVersion::ePdfVersion_1_5;
			break;
		case HOCRPdfExporter::PDFSettings::Version::PdfVersion_1_6:
			pdfVersion = PoDoFo::EPdfVersion::ePdfVersion_1_6;
			break;
		case HOCRPdfExporter::PDFSettings::Version::PdfVersion_1_7:
			pdfVersion = PoDoFo::EPdfVersion::ePdfVersion_1_7;
			break;
		}
		document = new PoDoFo::PdfStreamedDocument(filename.toLocal8Bit().data(), pdfVersion, encrypt);
	} catch(PoDoFo::PdfError& err) {
		errMsg = err.what();
		return nullptr;
	}

	QFontInfo finfo(defaultFont);

	// Attempt to load the default/fallback font to ensure it is valid
	try {
#if PODOFO_VERSION >= PODOFO_MAKE_VERSION(0,9,3)
		defaultPdfFont = document->CreateFontSubset(finfo.family().toLocal8Bit().data(), false, false, false, pdfFontEncoding);
#else
		defaultPdfFont = document->CreateFontSubset(finfo.family().toLocal8Bit().data(), false, false, pdfFontEncoding);
#endif
	} catch(PoDoFo::PdfError&) {
	}
	if(!defaultPdfFont) {
		errMsg = _("The PDF library could not load the font '%1'.").arg(defaultFont.family());
		return nullptr;
	}

	// Set PDF info
	PoDoFo::PdfInfo* pdfInfo = document->GetInfo();
	pdfInfo->SetProducer(settings.producer.toStdString());
	pdfInfo->SetCreator(settings.creator.toStdString());
	pdfInfo->SetTitle(settings.title.toStdString());
	pdfInfo->SetSubject(settings.subject.toStdString());
	pdfInfo->SetKeywords(settings.keywords.toStdString());
	pdfInfo->SetAuthor(settings.author.toStdString());

	return new HOCRPoDoFoPdfPrinter(document, pdfFontEncoding, defaultPdfFont, defaultFont.family(), defaultFont.pointSize());
}

HOCRPoDoFoPdfPrinter::HOCRPoDoFoPdfPrinter(PoDoFo::PdfStreamedDocument* document, const PoDoFo::PdfEncoding* fontEncoding, PoDoFo::PdfFont* defaultFont, const QString& defaultFontFamily, double defaultFontSize)
	: m_document(document), m_pdfFontEncoding(fontEncoding), m_defaultFont(defaultFont), m_defaultFontFamily(defaultFontFamily), m_defaultFontSize(defaultFontSize) {
	m_painter = new PoDoFo::PdfPainter();
}

HOCRPoDoFoPdfPrinter::~HOCRPoDoFoPdfPrinter() {
#if PODOFO_VERSION < PODOFO_MAKE_VERSION(0,9,3)
	delete m_pdfFontEncoding;
#endif
	delete m_document;
	delete m_painter;
	// Fonts are deleted by the internal PoDoFo font cache of the document
}

bool HOCRPoDoFoPdfPrinter::createPage(double width, double height, double offsetX, double offsetY, QString& /*errMsg*/) {
	PoDoFo::PdfPage* pdfpage = m_document->CreatePage(PoDoFo::PdfRect(0, 0, width, height));
	m_painter->SetPage(pdfpage);
	m_pageHeight = m_painter->GetPage()->GetPageSize().GetHeight();
	m_painter->SetFont(m_defaultFont);
	if(m_defaultFontSize > 0) {
		m_painter->GetFont()->SetFontSize(m_defaultFontSize);
	}
	m_offsetX = offsetX;
	m_offsetY = offsetY;
	return true;
}

void HOCRPoDoFoPdfPrinter::finishPage() {
	m_painter->FinishPage();
}

bool HOCRPoDoFoPdfPrinter::finishDocument(QString& errMsg) {
	try {
		m_document->Close();
	} catch(PoDoFo::PdfError& e) {
		errMsg = e.what();
		return false;
	}
	return true;
}

void HOCRPoDoFoPdfPrinter::setFontFamily(const QString& family, bool bold, bool italic) {
	float curSize = m_painter->GetFont()->GetFontSize();
	m_painter->SetFont(getFont(family, bold, italic));
	m_painter->GetFont()->SetFontSize(curSize);
}

void HOCRPoDoFoPdfPrinter::setFontSize(double pointSize) {
	m_painter->GetFont()->SetFontSize(pointSize);
}

void HOCRPoDoFoPdfPrinter::drawText(double x, double y, const QString& text) {
	PoDoFo::PdfString pdfString(reinterpret_cast<const PoDoFo::pdf_utf8*>(text.toUtf8().data()));
	m_painter->DrawText(m_offsetX + x, m_pageHeight - m_offsetY - y, pdfString);
}

void HOCRPoDoFoPdfPrinter::drawImage(const QRect& bbox, const QImage& image, const HOCRPdfExporter::PDFSettings& settings) {
	QImage img = convertedImage(image, settings.colorFormat, settings.conversionFlags);
	if(settings.colorFormat == QImage::Format_Mono) {
		img.invertPixels();
	}
#if PODOFO_VERSION >= PODOFO_MAKE_VERSION(0,9,3)
	PoDoFo::PdfImage pdfImage(m_document);
#else
	PoDoFo::PdfImageCompat pdfImage(m_document);
#endif
	pdfImage.SetImageColorSpace(img.format() == QImage::Format_RGB888 ? PoDoFo::ePdfColorSpace_DeviceRGB : PoDoFo::ePdfColorSpace_DeviceGray);
	int width = img.width();
	int height = img.height();
	int sampleSize = settings.colorFormat == QImage::Format_Mono ? 1 : 8;
	if(settings.compression == HOCRPdfExporter::PDFSettings::CompressZip) {
		// QImage has 32-bit aligned scanLines, but we need a continuous buffer
		int numComponents = settings.colorFormat == QImage::Format_RGB888 ? 3 : 1;
		int bytesPerLine = numComponents * ((width * sampleSize) / 8 + ((width * sampleSize) % 8 != 0));
		QVector<char> buf(bytesPerLine * height);
		for(int y = 0; y < height; ++y) {
			std::memcpy(buf.data() + y * bytesPerLine, img.scanLine(y), bytesPerLine);
		}
		PoDoFo::PdfMemoryInputStream is(buf.data(), bytesPerLine * height);
		pdfImage.SetImageData(width, height, sampleSize, &is, {PoDoFo::ePdfFilter_FlateDecode});
	} else if(settings.compression == HOCRPdfExporter::PDFSettings::CompressJpeg) {
		PoDoFo::PdfName dctFilterName(PoDoFo::PdfFilterFactory::FilterTypeToName(PoDoFo::ePdfFilter_DCTDecode));
		pdfImage.GetObject()->GetDictionary().AddKey(PoDoFo::PdfName::KeyFilter, dctFilterName);
		QByteArray data;
		QBuffer buffer(&data);
		img.save(&buffer, "jpg", settings.compressionQuality);
		PoDoFo::PdfMemoryInputStream is(data.data(), data.size());
		pdfImage.SetImageDataRaw(width, height, sampleSize, &is);
	} else if(settings.compression == HOCRPdfExporter::PDFSettings::CompressFax4) {
		PoDoFo::PdfName faxFilterName(PoDoFo::PdfFilterFactory::FilterTypeToName(PoDoFo::ePdfFilter_CCITTFaxDecode));
		pdfImage.GetObject()->GetDictionary().AddKey(PoDoFo::PdfName::KeyFilter, faxFilterName);
		PoDoFo::PdfDictionary decodeParams;
		decodeParams.AddKey("Columns", PoDoFo::PdfObject(PoDoFo::pdf_int64(img.width())));
		decodeParams.AddKey("Rows", PoDoFo::PdfObject(PoDoFo::pdf_int64(img.height())));
		decodeParams.AddKey("K", PoDoFo::PdfObject(PoDoFo::pdf_int64(-1))); // K < 0 --- Pure two-dimensional encoding (Group 4)
		pdfImage.GetObject()->GetDictionary().AddKey("DecodeParms", PoDoFo::PdfObject(decodeParams));
		CCITTFax4Encoder encoder;
		uint32_t encodedLen = 0;
		uint8_t* encoded = encoder.encode(img.constBits(), img.width(), img.height(), img.bytesPerLine(), encodedLen);
		PoDoFo::PdfMemoryInputStream is(reinterpret_cast<char*>(encoded), encodedLen);
		pdfImage.SetImageDataRaw(img.width(), img.height(), sampleSize, &is);
	}
	m_painter->DrawImage(m_offsetX + bbox.x(), m_pageHeight - m_offsetY - (bbox.y() + bbox.height()),
	                     &pdfImage, bbox.width() / double(image.width()), bbox.height() / double(image.height()));
}

double HOCRPoDoFoPdfPrinter::getAverageCharWidth() const {
	return m_painter->GetFont()->GetFontMetrics()->CharWidth(static_cast<unsigned char>('x'));
}
double HOCRPoDoFoPdfPrinter::getTextWidth(const QString& text) const {
	PoDoFo::PdfString pdfString(reinterpret_cast<const PoDoFo::pdf_utf8*>(text.toUtf8().data()));
	return m_painter->GetFont()->GetFontMetrics()->StringWidth(pdfString);
}


PoDoFo::PdfFont* HOCRPoDoFoPdfPrinter::getFont(QString family, bool bold, bool italic) {
	QString key = family + (bold ? "@bold" : "") + (italic ? "@italic" : "");
	auto it = m_fontCache.find(key);
	if(it == m_fontCache.end()) {
		if(family.isEmpty() || !m_fontDatabase.hasFamily(family)) {
			family = m_defaultFontFamily;
		}
		PoDoFo::PdfFont* font = nullptr;
		try {
#if PODOFO_VERSION >= PODOFO_MAKE_VERSION(0,9,3)
			font = m_document->CreateFontSubset(family.toLocal8Bit().data(), bold, italic, false, m_pdfFontEncoding);
#else
			font = m_document->CreateFontSubset(family.toLocal8Bit().data(), bold, italic, m_pdfFontEncoding);
#endif
			it = m_fontCache.insert(key, font);
		} catch(PoDoFo::PdfError& /*err*/) {
			it = m_fontCache.insert(key, m_defaultFont);;
		}
	}
	return it.value();
}


HOCRPdfExportDialog::HOCRPdfExportDialog(DisplayerToolHOCR* displayerTool, const HOCRDocument* hocrdocument, const HOCRPage* hocrpage, QWidget* parent)
	: QDialog(parent) {
	setLayout(new QVBoxLayout);
	m_widget = new HOCRPdfExportWidget(displayerTool, hocrdocument, hocrpage);
	layout()->addWidget(m_widget);

	QDialogButtonBox* bbox = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
	layout()->addWidget(bbox);
	connect(bbox, &QDialogButtonBox::accepted, this, &QDialog::accept);
	connect(bbox, &QDialogButtonBox::rejected, this, &QDialog::reject);
}

HOCRPdfExporter::PDFSettings HOCRPdfExportDialog::getPdfSettings() const {
	return m_widget->getPdfSettings();
}
