#pragma once

#include <QThread>
#include <QDebug>

using namespace std;

class Logger : public QThread
{
    Q_OBJECT

public:
	Logger();
	~Logger();

    void run() Q_DECL_OVERRIDE;
    void stop();
    void reset();
    void singleShot();
    
private:
    bool haltFlag = false;
    int input;
};