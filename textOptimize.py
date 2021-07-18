import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
import time
import os
import numpy as np

logSavingLocation = os.path.expanduser('~/Documents/Guild Wars 2/Chatlogs') # max 120
picText = open(os.path.join(logSavingLocation, "pic_text" + ".txt"), "r", encoding='utf8')

def main():
    global logSavingLocation
    global  picText
    #infoMsg.configure(text='start recording area (' + str(ScreenAreaX1) + ' | ' + str(ScreenAreaY1) + ')' + ' to (' + str(ScreenAreaX2) + ' | ' + str(ScreenAreaY2) + ')' )
    startTimer = time.time()
    #image = ImageGrab.grab(bbox=(ScreenAreaX1, ScreenAreaY1,                             ScreenAreaX2, ScreenAreaY2))

    f = open(os.path.join(logSavingLocation, "20210709_233602" + ".txt"), "r", encoding='utf8')
    filetext = f.read().split('\n')

    picText = picText.read().split('\n')
    newArray = []

    for word in filetext:
        if word == '':
            filetext.remove(word)

    for word in picText:
        if word == '':
            picText.remove(word)

    print(filetext)
    print(picText)

    for msg in picText:
       if not msg in filetext:
           newArray.append(msg)

    msgToFile = ''
    for singleMsg in newArray:
        msgToFile = msgToFile + singleMsg + '\n'

    if msgToFile == '':
        print('no new msg')

    print(newArray)
    print(msgToFile)

    endTimer = time.time()
    print(str(endTimer-startTimer) + 's')
    return

if __name__ == '__main__':
    main()