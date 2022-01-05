# vita_game_copier.py
import sys
import re
import requests
import webbrowser
import PySimpleGUI as sg
import os.path
import shutil
import csv


gamesout = []
patchesout = []
dlcout = []
repatchout = []
readdcontout = []
fileout = []

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
    [
        sg.Button("Show Details", enable_events=True, key="-DETAILS-")
    ]
]

arrow_column = [
    [sg.Button(button_text="⟶", enable_events=True, key="-ARROW R-")],
    [sg.Button(button_text="⟵", enable_events=True, key="-ARROW L-")]
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
        sg.Column(arrow_column),
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
        ciddict = {}
        try:
            dirlist = [ item for item in os.listdir(appfolder) if os.path.isdir(os.path.join(appfolder, item)) ]
        except:
            dirlist = []

        tsv = 'https://nopaystation.com/tsv/PSV_GAMES.tsv'
        headers={'user-agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.153 Safari/537.36 SE 2.X MetaSr 1.0'}
        with requests.Session() as s:
            r = s.get(tsv, headers=headers)
            content = r.content.decode('utf-8')
            reader = csv.DictReader(content.splitlines(), dialect='excel-tab')
            for row in reader:
                for directory in dirlist:
                    if row['Title ID']==directory:
                        gamedict[row['Name']] = row['Title ID']
                        ciddict[row['Name']] = row['Content ID']
        filelist = list(sorted(gamedict.keys()))
        window["-FILE LIST-"].update(filelist)
    elif event == "-DETAILS-": # Details button pressed
        try:
            filenow = values["-FILE LIST-"][-1]
            contentid = ciddict.get(filenow)
            gameid = gamedict.get(filenow)
            m = re.search(r'[^-]*(?!.*-)', contentid)
            url = "https://nopaystation.com/view/PSV/" + gameid + "/" + m.group(0) + "/1"
            webbrowser.open(url, new=0, autoraise=True)
            
        except Exception as e:
            print(e)

    elif event == "-ARROW R-":  # Right arrow button was pressed
        try:
            fileout += list(values["-FILE LIST-"])
            fileout = list(set(fileout))
            window["-SELECT LIST-"].update(fileout)
        
        except Exception as e:
            print(e)

    elif event == "-ARROW L-":  # Left arrow button was pressed
        try:
            window["-FILE LIST-"].update(set_to_index=[])
            filedel = list(values["-SELECT LIST-"])
            for e in filedel:
                if e in fileout:
                    fileout.remove(e)
            window["-SELECT LIST-"].update(fileout)
            
        except Exception as e:
            print(e)

    elif event == "Submit":  # Submit button was pressed
        try:
            if fileout:
                for f in fileout:
                    copy_game(f, values["-NPSFOLDER-"], values["-SDFOLDER-"])
        
        except Exception as e:
            print(e)

window.close()