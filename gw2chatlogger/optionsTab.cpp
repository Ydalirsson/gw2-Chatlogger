#include "optionsTab.h"
#include <QLabel>
#include <QPushButton>
#include <QSpinBox>
#include <QCheckBox>
#include <QGroupBox>
#include <QHBoxLayout>
#include <QGridLayout>
#include <QVBoxLayout>

OptionsTab::OptionsTab(QWidget* parent)
    : QWidget(parent)
{
    // Log file location row
    auto* logFileLocationLbl = new QLabel("Log file locaton:", this);
    auto* logFileLocationCurrentLbl = new QLabel("---", this);
    logFileLocationCurrentLbl->setWordWrap(true);
    auto* changeSaveLocBtn = new QPushButton("Change save location", this);

    auto* horizontalLayout = new QHBoxLayout;
    horizontalLayout->addWidget(logFileLocationLbl);
    horizontalLayout->addWidget(logFileLocationCurrentLbl);
    horizontalLayout->addWidget(changeSaveLocBtn);

    // Grid layout for points and SPM
    auto* gridLayout = new QGridLayout;

    auto* x1Lbl = new QLabel("X1:", this);
    auto* x2Lbl = new QLabel("X2:", this);
    auto* y2Lbl = new QLabel("Y2:", this);
    auto* newY1Edit = new QSpinBox(this); newY1Edit->setMaximum(10000);
    auto* savePointsBtn = new QPushButton("Save points", this);
    auto* x2CurrentLbl = new QLabel("0", this);
    auto* newY2Lbl = new QLabel("New Y2:", this);
    auto* newSpmEdit = new QSpinBox(this); newSpmEdit->setMaximum(240);
    auto* spmLbl = new QLabel("Screenshots/minute", this); spmLbl->setWordWrap(true);
    auto* newX1Edit = new QSpinBox(this); newX1Edit->setMaximum(10000);
    auto* newX2Lbl = new QLabel("New X2:", this);
    auto* y1CurrentLbl = new QLabel("0", this);
    auto* y1Lbl = new QLabel("Y1:", this);
    auto* newX1Lbl = new QLabel("New X1:", this);
    auto* spmNewLbl = new QLabel("New:", this);
    auto* newX2Edit = new QSpinBox(this); newX2Edit->setMaximum(10000);
    auto* newY2Edit = new QSpinBox(this); newY2Edit->setMaximum(10000);
    auto* y2CurrentLbl = new QLabel("0", this);
    auto* spmCurrentLbl = new QLabel("0", this);
    auto* newY1Lbl = new QLabel("New Y1:", this);
    auto* x1CurrentLbl = new QLabel("0", this);
    auto* saveSpmBtn = new QPushButton("Save", this);

    gridLayout->addWidget(x1Lbl, 0, 0);
    gridLayout->addWidget(x2Lbl, 1, 0);
    gridLayout->addWidget(y2Lbl, 1, 3);
    gridLayout->addWidget(newY1Edit, 2, 4);
    gridLayout->addWidget(savePointsBtn, 4, 4);
    gridLayout->addWidget(x2CurrentLbl, 1, 2);
    gridLayout->addWidget(newY2Lbl, 3, 3);
    gridLayout->addWidget(newSpmEdit, 5, 4);
    gridLayout->addWidget(spmLbl, 5, 0);
    gridLayout->addWidget(newX1Edit, 2, 2);
    gridLayout->addWidget(newX2Lbl, 3, 0);
    gridLayout->addWidget(y1CurrentLbl, 0, 4);
    gridLayout->addWidget(y1Lbl, 0, 3);
    gridLayout->addWidget(newX1Lbl, 2, 0);
    gridLayout->addWidget(spmNewLbl, 5, 3);
    gridLayout->addWidget(newX2Edit, 3, 2);
    gridLayout->addWidget(newY2Edit, 3, 4);
    gridLayout->addWidget(y2CurrentLbl, 1, 4);
    gridLayout->addWidget(spmCurrentLbl, 5, 2);
    gridLayout->addWidget(newY1Lbl, 2, 3);
    gridLayout->addWidget(x1CurrentLbl, 0, 2);
    gridLayout->addWidget(saveSpmBtn, 6, 4);

    // Language group
    auto* langCheckBoxGroup = new QGroupBox("Languages to log", this);
    auto* gridLayout2 = new QGridLayout;
    auto* engCheckBox = new QCheckBox("English", this);
    auto* gerCheckBox = new QCheckBox("Deutsch", this);
    auto* espCheckbox = new QCheckBox("Espanol", this);
    auto* fraCheckBox = new QCheckBox("Francais", this);

    gridLayout2->addWidget(engCheckBox, 0, 0);
    gridLayout2->addWidget(gerCheckBox, 0, 1);
    gridLayout2->addWidget(espCheckbox, 1, 0);
    gridLayout2->addWidget(fraCheckBox, 1, 1);
    langCheckBoxGroup->setLayout(gridLayout2);

    // Main layout
    auto* mainLayout = new QVBoxLayout(this);
    mainLayout->addLayout(horizontalLayout);
    mainLayout->addLayout(gridLayout);
    mainLayout->addWidget(langCheckBoxGroup);

    setLayout(mainLayout);

    x2CurrentLbl->setText(QString("324"));
}