#include "logger.h"

Logger::Logger()
{
    this->input = 0;
}
Logger::~Logger()
{

}

void Logger::run()
{
    static int i = 0;
    while (true) {
        if (haltFlag)
        {  
            break;
        }
        else
        {
            qDebug() << i;
            i++;
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

void Logger::reset()
{
    this->haltFlag = false;
}
