# vita_game_copier.py
import sys
import PySimpleGUI as sg
import os.path
import shutil
import csv


gamesout = []
patchesout = []
dlcout = []
repatchout = []
readdcontout = []

# Left Column
file_list_column = [
    [
        sg.Text("NPS folder on PC"),
        sg.In(size=(25, 1), enable_events=True, key="-NPSFOLDER-"),
        sg.FolderBrowse(),
    ],
    [
        sg.Listbox(
            values=[], select_mode='extended', enable_events=True, size=(48, 20), key="-FILE LIST-"
        )
    ],
]

# Middle Column
copy_column = [
    [
        sg.Text("SD Card on USB"),
        sg.In(size=(25, 1), enable_events=True, key="-SDFOLDER-"),
        sg.FolderBrowse(),
    ],
    [
        sg.Listbox(
            values=[], select_mode='extended', enable_events=True, size=(48, 20), key="-SELECT LIST-"
        )
    ],
    [
        sg.Checkbox('Patch', default=True, key='cbpatch'),
        sg.Checkbox('DLC', default=True, key='cbdlc'),
        sg.Checkbox('Repatch', default=True, key='cbrepatch'),
        sg.Checkbox('Readdcont', default=True, key='cbreaddcont')
    ],
    [
        sg.Text("Above games will be copied to SD"),
        sg.Submit()
    ]
]

# Right Column
output_column = [
    [sg.Text("Copied Games", size=(10, None)),
    sg.Listbox(
        values=[], select_mode='extended', enable_events=True, size=(40, 5), key="-GAMES-")
    ],
    [sg.Text("Copied Patches", size=(10, None)),
    sg.Listbox(
        values=[], select_mode='extended', enable_events=True, size=(40, 5), key="-PATCHES-")
    ],
    [sg.Text("Copied DLC", size=(10, None)),
    sg.Listbox(
        values=[], select_mode='extended', enable_events=True, size=(40, 5), key="-DLC-")
    ],
    [sg.Text("Copied Repatch", size=(10, None)),
    sg.Listbox(
        values=[], select_mode='extended', enable_events=True, size=(40, 5), key="-REPATCH-")
    ],
    [sg.Text("Copied Readdcont", size=(10, None)),
    sg.Listbox(
        values=[], select_mode='extended', enable_events=True, size=(40, 5), key="-READDCONT-")
    ]
]

# ----- Full layout -----
layout = [
    [
        sg.Column(file_list_column),
        sg.VSeperator(),
        sg.Column(copy_column),
        sg.VSeparator(),
        sg.Column(output_column)
    ]
]

window = sg.Window("Vita Game Copier", layout)

# Code that copies game and extras
def copy_game(gamename, path, sdpath):
    folder = gamedict.get(gamename)
    apppath = os.path.join(path, "app", folder)
    sdapppath = os.path.join(sdpath, "app", folder)
    patchpath = os.path.join(path, "patch", folder)
    sdpatchpath = os.path.join(sdpath, "patch", folder)
    addcontpath = os.path.join(path, "addcont", folder)
    sdaddcontpath = os.path.join(sdpath, "addcont", folder)
    readdcontpath = os.path.join(path, "readdcont", folder)
    sdreaddcontpath = os.path.join(sdpath, "readdcont", folder)
    repatchpath = os.path.join(path, "repatch", folder)
    sdrepatchpath = os.path.join(sdpath, "repatch", folder)
    
    if os.path.isdir(apppath):
        try:
            shutil.copytree(apppath, sdapppath)
            gamesout.append(gamename)
            window["-GAMES-"].update(gamesout)
        except:
            print("Game not successfully copied")
        if values["cbpatch"] == True:
            try:
                shutil.copytree(patchpath, sdpatchpath)
                patchesout.append(gamename)
                window["-PATCHES-"].update(patchesout)
            except:
                print("Patch not successfully copied")
        if values["cbdlc"] == True:
            try:
                shutil.copytree(addcontpath, sdaddcontpath)
                dlcout.append(gamename)
                window["-DLC-"].update(dlcout)
            except:
                print("DLC not successfully copied")
        if values["cbrepatch"] == True:
            try:
                shutil.copytree(repatchpath, sdrepatchpath)
                repatchout.append(gamename)
                window["-REPATCH-"].update(repatchout)
            except:
                print("Repatch not successfully copied")
        if values["cbreaddcont"] == True:
            try:
                shutil.copytree(readdcontpath, sdreaddcontpath)
                readdcontout.append(gamename)
                window["-READDCONT-"].update(readdcontout)
            except:
                print("Readdcont not successfully copied")

#For Pyinstaller to work
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Run the Event Loop
while True:
    event, values = window.read()
    if event in ["Exit", sg.WIN_CLOSED]:
        break
    # Folder name was filled in, make a list of files in the folder
    if event == "-NPSFOLDER-":
        folder = values["-NPSFOLDER-"]
        appfolder = os.path.join(folder, "app")
        gamedict = {}
        try:
            dirlist = [ item for item in os.listdir(appfolder) if os.path.isdir(os.path.join(appfolder, item)) ]
        except:
            dirlist = []

        filename = resource_path('PSV_GAMES.tsv')
        with open(filename, encoding="utf-8") as tsvfile:
            reader = csv.DictReader(tsvfile, dialect='excel-tab')
            for row in reader:
                for directory in dirlist:
                    if row['Title ID']==directory:
                        gamedict[row['Name']] = row['Title ID']
        filelist = list(sorted(gamedict.keys()))
        window["-FILE LIST-"].update(filelist)
    elif event == "-FILE LIST-":  # A file was chosen from the listbox
        try:
            fileout = list(values["-FILE LIST-"])
            window["-SELECT LIST-"].update(fileout)
        except:
            pass
    elif event == "Submit":  # Submit button was pressed
        try:
            fileout = list(values["-FILE LIST-"])
            if fileout:
                for f in fileout:
                    copy_game(f, values["-NPSFOLDER-"], values["-SDFOLDER-"])
        except:
            print("failed")

window.close()