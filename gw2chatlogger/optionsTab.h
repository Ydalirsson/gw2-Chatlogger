#pragma once
#include <QWidget>

class QLabel;
class QPushButton;
class QSpinBox;
class QCheckBox;
class QGroupBox;
class QHBoxLayout;
class QGridLayout;
class QVBoxLayout;

class OptionsTab : public QWidget {
    Q_OBJECT
public:
    explicit OptionsTab(QWidget* parent = nullptr);

private:
    // Labels
    QLabel* logFileLocationLbl;
    QLabel* logFileLocationCurrentLbl;
    QLabel* x1Lbl;
    QLabel* x2Lbl;
    QLabel* y1Lbl;
    QLabel* y2Lbl;
    QLabel* newX1Lbl;
    QLabel* newX2Lbl;
    QLabel* newY1Lbl;
    QLabel* newY2Lbl;
    QLabel* x1CurrentLbl;
    QLabel* x2CurrentLbl;
    QLabel* y1CurrentLbl;
    QLabel* y2CurrentLbl;
    QLabel* spmLbl;
    QLabel* spmNewLbl;
    QLabel* spmCurrentLbl;

    // Buttons
    QPushButton* changeSaveLocBtn;
    QPushButton* savePointsBtn;
    QPushButton* saveSpmBtn;

    // Spinboxes
    QSpinBox* newX1Edit;
    QSpinBox* newX2Edit;
    QSpinBox* newY1Edit;
    QSpinBox* newY2Edit;
    QSpinBox* newSpmEdit;

    // Checkboxes
    QCheckBox* engCheckBox;
    QCheckBox* gerCheckBox;
    QCheckBox* espCheckBox;
    QCheckBox* fraCheckBox;

    // Layouts
    QHBoxLayout* horizontalLayout;
    QGridLayout* gridLayout;
    QGridLayout* gridLayout2;
    QVBoxLayout* mainLayout;

    // Group
    QGroupBox* langCheckBoxGroup;
};

