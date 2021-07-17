import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'Tesseract-OCR\tesseract.exe'
from PIL import ImageGrab
import win32gui
import pyautogui
import time
from tkinter import *
from tkinter import ttk, filedialog
import os
import threading
import configparser
import numpy as np
import cv2

logSavingLocation = os.path.expanduser('~/Documents/Guild Wars 2/Chatlogs') # max 120
filename = ''
threadStopped = False   # flag for thread execution
ScreenAreaX1 = 30
ScreenAreaY1 = 1620
ScreenAreaX2 = 825
ScreenAreaY2 = 2070
spm = 60          # chat scans per minutes
checkedEN = True
checkedDE = False
checkedES = False
checkedFR = False

ocrLanguages = ''


clear = lambda: os.system('cls')

def checkActiveWindow():
    foregroundWindowName = win32gui.GetWindowText(win32gui.GetForegroundWindow())
    return True if (foregroundWindowName == 'Guild Wars 2') else False


def createNewSessionLogFile():
    global filename
    global logSavingLocation
    filename = time.strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(logSavingLocation, filename + ".txt"), 'w') as fp:
        pass
    return


def prepareLogging():
    if not os.path.exists(logSavingLocation):
        os.makedirs(logSavingLocation)
    createNewSessionLogFile()
    button_1["state"] = "disabled"
    button_2["state"] = "normal"
    button_3["state"] = "disabled"
    button_4["state"] = "disabled"
    button_5["state"] = "disabled"
    notebook.tab(optionsTab, state="disabled")

    global threadStopped
    threadStopped = False
    threadLogging = threading.Thread(target=doLogging)
    threadLogging.start()


def doLogging():
    global threadStopped
    global filename
    while not threadStopped:
        if checkActiveWindow():
            clear()
            image = ImageGrab.grab(bbox=(ScreenAreaX1, ScreenAreaY1,
                                         ScreenAreaX2, ScreenAreaY2))
            string = pytesseract.image_to_string(image, config=r'--psm 6 --oem 3', lang=ocrLanguages)

            # TODO: optimize text

            f = open(os.path.join(logSavingLocation, filename + ".txt"), "a", encoding='utf8')
            f.write(string)
            f.close()
            time.sleep(1 / (spm / 60))  # in seconds
            infoMsg.configure(text='Chat is logging')
        else:
            infoMsg.configure(text='GW2 is not the active and focused window')
    infoMsg.configure(text='Chat logging stopped')


def stopLogging():
    global threadStopped
    threadStopped = True
    button_1["state"] = "normal"
    button_2["state"] = "disabled"
    button_3["state"] = "normal"
    button_4["state"] = "normal"
    button_5["state"] = "normal"
    notebook.tab(optionsTab, state="normal")


def tryLogging():
    infoMsg.configure(text='start recording area (' + str(ScreenAreaX1) + ' | ' + str(ScreenAreaY1) + ')' + ' to (' + str(ScreenAreaX2) + ' | ' + str(ScreenAreaY2) + ')' )
    startTimer = time.time()
    image = ImageGrab.grab(bbox=(ScreenAreaX1, ScreenAreaY1,
                                     ScreenAreaX2, ScreenAreaY2))

    f = open(os.path.join(logSavingLocation, "20210711_232325" + ".txt"), "r", encoding='utf8')
    filetext = f.read().split('\n')


    string = pytesseract.image_to_string(image, config=r'--psm 6 --oem 3', lang=ocrLanguages)
    picText = string.split('\n')
    newArray = []
    print(filetext)
    print(picText)
    for row in filetext:
        for msg in picText:
            if row == msg:
                continue
            else:
                newArray.append(msg)
    print(newArray)

    endTimer = time.time()
    logEntryView.configure(text=string + "\ntime to convert: " + str(endTimer-startTimer) + 's')
    infoMsg.configure(text='check "Logger view"-tab ' + str(ocrLanguages))
    return


def drawArea():
    global ScreenAreaX1
    global ScreenAreaY1
    global ScreenAreaX2
    global ScreenAreaY2

    image = pyautogui.screenshot()
    image = np.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    x, y, w, h = cv2.selectROI(windowName="Select chatbox", img=image)
    ScreenAreaX1 = x
    ScreenAreaY1 = y
    ScreenAreaX2 = x + w
    ScreenAreaY2 = y + h
    cv2.destroyAllWindows()

    config = configparser.ConfigParser()
    config.read(os.path.join(logSavingLocation, "settings" + ".ini"))
    config.set('recording', 'x1', str(ScreenAreaX1))
    config.set('recording', 'y1', str(ScreenAreaY1))
    config.set('recording', 'x2', str(ScreenAreaX2))
    config.set('recording', 'y2', str(ScreenAreaY2))
    cfgFile = open(os.path.join(logSavingLocation, "settings" + ".ini"), "w")
    config.write(cfgFile)
    cfgFile.close()
    updateGUI()
    return


def saveArea():
    global ScreenAreaX1
    global ScreenAreaY1
    global ScreenAreaX2
    global ScreenAreaY2

    ScreenAreaX1 = int(x1Entry.get())
    ScreenAreaY1 = int(y1Entry.get())
    ScreenAreaX2 = int(x2Entry.get())
    ScreenAreaY2 = int(y2Entry.get())

    config = configparser.ConfigParser()
    config.read(os.path.join(logSavingLocation, "settings" + ".ini"))
    config.set('recording', 'x1', str(ScreenAreaX1))
    config.set('recording', 'y1', str(ScreenAreaY1))
    config.set('recording', 'x2', str(ScreenAreaX2))
    config.set('recording', 'y2', str(ScreenAreaY2))
    cfgFile = open(os.path.join(logSavingLocation, "settings" + ".ini"), "w")
    config.write(cfgFile)
    cfgFile.close()
    updateGUI()
    return


def saveSPM():
    global spm
    spm = int(SpmEntry.get())
    config = configparser.ConfigParser()
    config.read(os.path.join(logSavingLocation, "settings" + ".ini"))
    config.set('recording', 'spm', str(spm))
    cfgFile = open(os.path.join(logSavingLocation, "settings" + ".ini"), "w")
    config.write(cfgFile)
    cfgFile.close()
    updateGUI()
    return


def updateLanguageStr():
    global checkedEN
    global checkedDE
    global checkedES
    global checkedFR
    global ocrLanguages
    ocrLanguages = ''
    activeLangCounter = 0
    if checkedEN:
        activeLangCounter += 1
    if checkedDE:
        activeLangCounter += 1
    if checkedES:
        activeLangCounter += 1
    if checkedFR:
        activeLangCounter += 1

    if activeLangCounter == 0:
        ocrLanguages = 'eng'
    elif activeLangCounter == 1:
        if checkedEN:
            ocrLanguages = 'eng'
        if checkedDE:
            ocrLanguages = 'deu'
        if checkedES:
            ocrLanguages = 'spa'
        if checkedFR:
            ocrLanguages = 'fra'
    elif activeLangCounter > 1:
        arrStr = []
        if checkedEN:
            arrStr.append('eng')
        if checkedDE:
            arrStr.append('deu')
        if checkedES:
            arrStr.append('spa')
        if checkedFR:
            arrStr.append('fra')
        for aStr in arrStr:
            if len(ocrLanguages) == 0:
                ocrLanguages = arrStr[0]
            else:
                ocrLanguages = ocrLanguages + '+' + aStr
        print(ocrLanguages)
    return

def setActiveLanguage():
    global checkedEN
    global checkedDE
    global checkedES
    global checkedFR
    global checked1, checked2, checked3, checked4

    checkedEN = checked1.get()
    checkedDE = checked2.get()
    checkedES = checked3.get()
    checkedFR = checked4.get()

    config = configparser.ConfigParser()
    config.read(os.path.join(logSavingLocation, "settings" + ".ini"))
    config.set('languages', 'en', str(checkedEN))
    config.set('languages', 'de', str(checkedDE))
    config.set('languages', 'es', str(checkedES))
    config.set('languages', 'fr', str(checkedFR))
    cfgFile = open(os.path.join(logSavingLocation, "settings" + ".ini"), "w")
    config.write(cfgFile)
    cfgFile.close()

    updateLanguageStr()
    return


def changeSaveLocation():
    global logSavingLocation
    newLogSavingLocation = filedialog.askdirectory()
    config = configparser.ConfigParser()
    config.read(os.path.join(logSavingLocation, "settings" + ".ini"))
    config.set('saving folders', 'path', str(newLogSavingLocation))
    cfgFile = open(os.path.join(logSavingLocation, "settings" + ".ini"), "w")
    config.write(cfgFile)
    cfgFile.close()
    logSavingLocation = newLogSavingLocation
    updateGUI()
    return


def updateGUI():
    global logSavingLocation
    global ScreenAreaX1
    global ScreenAreaY1
    global ScreenAreaX2
    global ScreenAreaY2
    global spm
    global checkedEN
    global checkedDE
    global checkedES
    global checkedFR
    global checked1
    global checked2
    global checked3
    global checked4

    savingFolderMsg.configure(text=logSavingLocation)
    x1Msg.configure(text=ScreenAreaX1)
    y1Msg.configure(text=ScreenAreaY1)
    x2Msg.configure(text=ScreenAreaX2)
    y2Msg.configure(text=ScreenAreaY2)
    SpmMessage.configure(text=spm)
    checked1.set(checkedEN)
    checked2.set(checkedDE)
    checked3.set(checkedES)
    checked4.set(checkedFR)
    return


def readSettings():
    global logSavingLocation
    global ScreenAreaX1
    global ScreenAreaY1
    global ScreenAreaX2
    global ScreenAreaY2
    global spm
    global checkedEN
    global checkedDE
    global checkedES
    global checkedFR
    global ocrLanguages

    config = configparser.ConfigParser()
    config.read(os.path.join(logSavingLocation, "settings" + ".ini"))
    config.sections()

    logSavingLocation = config.get("saving folders", "path")

    ScreenAreaX1 = config.getint("recording", "x1")
    ScreenAreaY1 = config.getint("recording", "y1")
    ScreenAreaX2 = config.getint("recording", "x2")
    ScreenAreaY2 = config.getint("recording", "y2")
    spm = config.getint("recording", "spm")

    checkedEN = config.getboolean("languages", "en")
    checkedDE = config.getboolean("languages", "de")
    checkedES = config.getboolean("languages", "es")
    checkedFR = config.getboolean("languages", "fr")

    updateLanguageStr()
    updateGUI()
    return


# ***************
# Building GUI
# ***************

root = Tk()

notebook = ttk.Notebook(root)
notebook.grid()
controlTab = Frame(notebook, width=500, height=500)
viewLogTab = Frame(notebook, width=500, height=500)
optionsTab = Frame(notebook, width=500, height=500)
notebook.add(controlTab, text="Control")
notebook.add(viewLogTab, text="Logger view")
notebook.add(optionsTab, text="Options")

# ***************
# Control tab
# ***************
PAD = 10
button_1 = Button(controlTab, text="Record", padx=PAD, pady=PAD, command= prepareLogging)
button_2 = Button(controlTab, text="Stop", padx=PAD, pady=PAD, command= stopLogging)
button_3 = Button(controlTab, text="Try", padx=PAD, pady=PAD, command= tryLogging)
button_4 = Button(controlTab, text="Set chat box area", padx=PAD, pady=PAD, command= drawArea)
button_5 = Button(controlTab, text="New log session", padx=PAD, pady=PAD, command= createNewSessionLogFile)

infoLbl = Label(controlTab, text="Info box:")
infoMsg = Message(controlTab, text="")

# ***************
# View log tab
# ***************
logEntryLbl = Label(viewLogTab, text="Current log:")
logEntryView = Message(viewLogTab, text="")

# ***************
# Options tab
# ***************
x1Current = Label(optionsTab, text="X1:")
y1Current = Label(optionsTab, text="Y1:")
x2Current = Label(optionsTab, text="X2:")
y2Current = Label(optionsTab, text="Y2:")

x1Msg = Message(optionsTab, text=ScreenAreaX1)
y1Msg = Message(optionsTab, text=ScreenAreaY1)
x2Msg = Message(optionsTab, text=ScreenAreaX2)
y2Msg = Message(optionsTab, text=ScreenAreaY2)

x1New = Label(optionsTab, text="New X1:")
y1New = Label(optionsTab, text="New Y1:")
x2New = Label(optionsTab, text="New X2:")
y2New = Label(optionsTab, text="New Y2:")

x1Entry = Entry(optionsTab)
y1Entry = Entry(optionsTab)
x2Entry = Entry(optionsTab)
y2Entry = Entry(optionsTab)
saveAreaBtn = Button(optionsTab, text="Save points", command= saveArea)

SpmCurrent = Label(optionsTab, text="Screenshots/\nminute:")
SpmMessage = Message(optionsTab, text=spm)
SpmNew = Label(optionsTab, text="New:")
SpmEntry = Entry(optionsTab)
SpmSave = Button(optionsTab, text="Save", command= saveSPM)

languagesCurrent = Label(optionsTab, text="Languages\nto log")
checked1 = BooleanVar()
checked2 = BooleanVar()
checked3 = BooleanVar()
checked4 = BooleanVar()
langEN = Checkbutton(optionsTab, text="English", variable=checked1, onvalue=True, offvalue=False, command= setActiveLanguage)
langDE = Checkbutton(optionsTab, text="Deutsch", variable=checked2, onvalue=True, offvalue=False, command= setActiveLanguage)
langES = Checkbutton(optionsTab, text="Español", variable=checked3, onvalue=True, offvalue=False, command= setActiveLanguage)
langFR = Checkbutton(optionsTab, text="Français", variable=checked4, onvalue=True, offvalue=False, command= setActiveLanguage)

savingFolder = Label(optionsTab, text="Log file location:")
savingFolderMsg = Message(optionsTab, text=logSavingLocation)
changFolderBtn  = Button(optionsTab, text="Change save location", command= changeSaveLocation)


# ***************
# Binding to grid
# ***************
button_1.grid(row=1, column=1)
button_2.grid(row=1, column=2)
button_3.grid(row=1, column=3)
button_4.grid(row=1, column=4)
button_5.grid(row=1, column=5)

infoLbl.grid(row=2, column=1)
infoMsg.grid(row=2, column=2)
logEntryLbl.grid(row=1, column=1)
logEntryView.grid(row=1, column=2)

x1Current.grid(row=1, column=1)
y1Current.grid(row=1, column=3)
x2Current.grid(row=2, column=1)
y2Current.grid(row=2, column=3)
x1Msg.grid(row=1, column=2)
y1Msg.grid(row=1, column=4)
x2Msg.grid(row=2, column=2)
y2Msg.grid(row=2, column=4)
x1New.grid(row=3, column=1)
y1New.grid(row=3, column=3)
x2New.grid(row=4, column=1)
y2New.grid(row=4, column=3)
x1Entry.grid(row=3, column=2)
y1Entry.grid(row=3, column=4)
x2Entry.grid(row=4, column=2)
y2Entry.grid(row=4, column=4)
saveAreaBtn.grid(row=5, column=4)

SpmCurrent.grid(row=6, column=1)
SpmMessage.grid(row=6, column=2)
SpmNew.grid(row=6, column=3)
SpmEntry.grid(row=6, column=4)
SpmSave.grid(row=7, column=4)

languagesCurrent.grid(row=8, column=1)
langEN.grid(row=9, column=1)
langDE.grid(row=9, column=2)
langES.grid(row=10, column=1)
langFR.grid(row=10, column=2)

savingFolder.grid(row=11, column=1)
savingFolderMsg.grid(row=11, column=2)
changFolderBtn.grid(row=11, column=4)

# ***********************
# init program and files
# ***********************
if not os.path.exists(logSavingLocation):
    os.makedirs(logSavingLocation)

if not os.path.isfile(os.path.join(logSavingLocation, "settings" + ".ini")):
    cfgFile = open(os.path.join(logSavingLocation, "settings" + ".ini"), "w")
    config = configparser.ConfigParser()

    config.add_section('saving folders')
    config.set('saving folders', 'path', logSavingLocation)

    config.add_section('recording')
    config.set('recording', 'X1', '30')
    config.set('recording', 'Y1', '1620')
    config.set('recording', 'X2', '825')
    config.set('recording', 'Y2', '2070')
    config.set('recording', 'spm', '4')

    config.add_section('languages')
    config.set('languages', 'EN', 'True')
    config.set('languages', 'DE', 'False')
    config.set('languages', 'ES', 'False')
    config.set('languages', 'FR', 'False')

    config.write(cfgFile)
    cfgFile.close()

readSettings()

root.title("GW2-Chatlogger")
root.geometry("600x600")
root.mainloop()
