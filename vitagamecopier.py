# vita_game_copier.py
import sys
import re
import requests
import webbrowser
import PySimpleGUI as sg
import os.path
from shutil import *
import csv
import ctypes
from ftplib import FTP
import ftplib
import ftputil
import hashlib


gamesout = []
patchesout = []
dlcout = []
repatchout = []
readdcontout = []
dictout = {"app": gamesout, "patch": patchesout, "DLC": dlcout, "repatch": repatchout, "readdcont": readdcontout}
fileout = []
dirlist = []
gamedict = {}
ciddict = {}
ftpmode = False
system = 'Vita'
usedbytes = 0
filelist = []
ftp = FTP()
appfolder = ''

class MySession(ftplib.FTP):

    def __init__(self, host, port):
        """Act like ftplib.FTP's constructor but connect to another port."""
        ftplib.FTP.__init__(self)
        self.connect(host, port)

sg.theme('DarkGrey11')

# Left Column
file_list_column = [
    [
        sg.Text("Mode"),
        sg.Stretch(),
        sg.Text("System")
    ],
    [
        sg.Combo(['FTP', 'USB'], enable_events=True, default_value='USB', key='-MODE-'),
        sg.Stretch(),
        sg.Combo(['PSP', 'PSX', 'Vita'], enable_events=True, default_value='Vita', key='-SYSTEM-')
    ],
    [
        sg.Text("NPS folder on PC"),
        sg.In(size=(25, None), enable_events=True, key="-NPS FOLDER-"),
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
        sg.Text(text="SD Card on USB", key="-SD TEXT-"),
        sg.In(size=(25, None), enable_events=True, key="-SD FOLDER-"),
        sg.FolderBrowse(key="-BTN BROWSE-"), sg.Button("Connect", enable_events=True, visible=False, key="-BTN CONNECT-")
    ],
    [
        sg.Listbox(
            values=[], select_mode='extended', enable_events=True, size=(48, 20), key="-SELECT LIST-"
        )
    ],
    [
        sg.Checkbox('Patch', default=True, key='-CB PATCH-'),
        sg.Checkbox('DLC', default=True, key='-CB DLC-'),
        sg.Checkbox('Repatch', default=True, key='-CB REPATCH-'),
        sg.Checkbox('Readdcont', default=True, key='-CB READDCONT-')
    ],
    [
        sg.Text("Total space available on SD:", size=(23, None), key="-SD FREETEXT-"),
        sg.In(size=(22, None), enable_events=True, key="-SD SIZE-")
    ],
    [
        sg.Text("Total size of selected games:", size=(23, None)),
        sg.In(size=(22, None), enable_events=True, key="-SIZE-")
    ],
    [
        sg.Text("Above games will be copied to SD"),
        sg.Submit()
    ]
]

# stdout Column

stdout_column = [
    [
        sg.Text("Output")
    ],
    [
        sg.Output(size=(172, 10), expand_x=True)
    ]
]

# Right Column
output_column = [
    [sg.Text("Copied Games", size=(10, None)),
    sg.Listbox(
        values=[], enable_events=True, size=(40, 5), key="-GAMES-")
    ],
    [sg.Text("Copied Patches", size=(10, None)),
    sg.Listbox(
        values=[], enable_events=True, size=(40, 5), key="-PATCHES-")
    ],
    [sg.Text("Copied DLC", size=(10, None)),
    sg.Listbox(
        values=[], enable_events=True, size=(40, 5), key="-DLC-")
    ],
    [sg.Text("Copied Repatch", size=(10, None)),
    sg.Listbox(
        values=[], enable_events=True, size=(40, 5), key="-REPATCH-")
    ],
    [sg.Text("Copied Readdcont", size=(10, None)),
    sg.Listbox(
        values=[], enable_events=True, size=(40, 5), key="-READDCONT-")
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
    ],
    [
        sg.Column(stdout_column)
    ]
]

window = sg.Window("Vita Game Copier", layout, resizable=True, icon="cat512_54h_icon.ico")

def format_bytes(size):
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'kilo', 2: 'mega', 3: 'giga', 4: 'tera'}
    while size > power:
        size /= power
        n += 1
    size = '{0:.2f}'.format(size)
    return size, power_labels[n]+'bytes'

def get_free_space(drive):
    fb = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(drive), None, None, ctypes.pointer(fb))
    return fb.value

def copytree(src, dst, symlinks=False, ignore=None):
    names = os.listdir(src)
    ignored_names = ignore(src, names) if ignore is not None else set()
    if not os.path.isdir(dst): # This one line does the trick
        os.makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy2(srcname, dstname)
                print(".", end="")
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        copystat(src, dst)
    except OSError as why:
        if WindowsError is None or not isinstance(why, WindowsError):
            errors.extend((src, dst, str(why)))
    if errors:
        raise Error(errors)

def print_out(type, bool):
    if bool == True:
        print("\n --{} Copied!".format(type))
    if bool == False:
        print(" --No {} Found.".format(type))

def copy_with_callback(sourceFile, destinationFile, callbackFunction):
    chunk = 2**16
    sourceSize = os.path.getsize(sourceFile)
    destSize = 0
    with open(sourceFile, 'rb') as fSrc:
        with open(destinationFile, 'wb') as fDest:
            while destSize < sourceSize:
                data = fSrc.read(chunk)
                if data == 0:
                    return
                fDest.write(data)
                destSize += len(data)
                callbackFunction(sourceSize, destSize)
            

def example_callback_function(srcSize, dstSize):
    ''' Just an example with print.  Your viewer code will vary '''
    percent = dstSize / srcSize
    print('Copy ', "{:.2f}".format(percent * 100), ' percent complete.')

def md5check(path):
    file = open(path, "rb")
    content = file.read()
    md5 = hashlib.md5()
    md5.update(content)
    return md5.hexdigest()

def usb_go(sdpatho, fldtype, filename, path, gamename):
    fldtype2 = "Game" if fldtype in ("app", "pspemu/ISO", "pspemu/PSP/GAME") else fldtype[:1].upper() + fldtype[1:]
    path = os.path.join(path, fldtype, filename)
    sdpath = os.path.join(sdpatho, fldtype, filename)
    if system == "Vita":
        copytree(path, sdpath)
        print("\n --{} Copied!".format(fldtype2))
        dictout.get(fldtype).append(gamename)
    elif system == "PSX":
        copytree(path, sdpath)
        print("\n --{} Copied!".format(fldtype2))
        dictout.get("app").append(gamename)
    elif os.path.isfile(sdpath):
        print(" --{} already exists.".format(fldtype2))
    else:
        isodir = os.path.join(sdpatho, fldtype)
        if os.path.isdir(isodir) != True:
            os.makedirs(isodir)
        srccrc = md5check(path)
        copy_with_callback(path, sdpath, example_callback_function)
        print("\n --{} Copied!".format(fldtype2))
        destcrc = md5check(sdpath)
        if srccrc == destcrc:
            print("MD5 Checksum verified.")
        else:
            print("MD5 Checksum failed.")
        dictout.get("app").append(gamename)

# Code that copies game and extras
def copy_game(gamename, path, sdpath):  # sourcery no-metrics
    if system == "PSP":
        fldtype = "pspemu/ISO"
        filename = gamedict.get(gamename)
        gamefile = os.path.join(path, fldtype, filename)
        gamepath = ''

    if system == "PSX":
        fldtype = "pspemu/PSP/GAME"
        filename = gamedict.get(gamename) # Convert human name to Title ID
        gamepath = os.path.join(path, fldtype, filename)
        gamefile = ''

    elif system == "Vita":
        fldtype = "app"
        filename = gamedict.get(gamename) # Convert human name to Title ID
        gamepath = os.path.join(path, fldtype, filename)
        gamefile = ''

    if os.path.isdir(gamepath) or os.path.isfile(gamefile):
        try:
            usb_go(sdpath, fldtype, filename, path, gamename)
        except:
            print_out("Game", False)
        
        if values["-CB PATCH-"] == True:
            try:
                fldtype = "patch"
                usb_go(sdpath, fldtype, filename, path, gamename)
            except:
                print_out("Patch", False)

        if values["-CB DLC-"] == True:
            try:
                fldtype = "DLC"
                usb_go(sdpath, fldtype, filename, path, gamename)
            except:
                print_out("DLC", False)

        if values["-CB REPATCH-"] == True:
            try:
                fldtype = "repatch"
                usb_go(sdpath, fldtype, filename, path, gamename)
            except:
                print_out("Repatch", False)

        if values["-CB READDCONT-"] == True:
            try:
                fldtype = "readdcont"
                usb_go(sdpath, fldtype, filename, path, gamename)
                print("\n")
            except:
                print_out("Readdcont", False)
                print("\n")
    

def upload_dir(localDir, ftpDir):
    list = os.listdir(localDir)
    count = 0
    #print(list)
    for fname in list:
        #print(fname)
        if os.path.isdir(localDir + fname):
            if(ftp_host.path.exists(ftpDir + fname) != True):
                ftp_host.mkdir(ftpDir + fname)
                upload_dir(localDir + fname + "/", ftpDir + fname + "/")
        elif (ftp_host.upload_if_newer(localDir + fname, ftpDir + fname)):
            print(".", end="")
            count += 1
        else:
            print("", end="")
    return count

def ftp_go(ftproot, fldtype, filename, path, gamename):
    ftpdir = "{}{}/".format(ftproot, fldtype)
    ftpfolder = "{}{}/".format(ftpdir, filename)
    localfolder = "{}/".format(os.path.join(path, fldtype, filename))
    ftp_host.chdir(ftpdir)
    fldtype2 = "Game" if fldtype in ("app", "pspemu/ISO", "pspemu/PSP/GAME") else fldtype[:1].upper() + fldtype[1:]

    if (ftp_host.path.exists(ftpfolder)):
        print(".", end="")
    elif system in ("PSX", "Vita"):
        ftp_host.mkdir(filename)
    if system in ("PSX", "Vita"):
        count = upload_dir(localfolder, ftpfolder)
    else:
        count = 0
        if ftp_host.upload_if_newer(localfolder, ftpfolder):
            count += 1

    if count == 0:
        print(" --{} already exists.".format(fldtype2))
    else:
        print_out(fldtype2, True)
        if fldtype in ("pspemu/ISO", "pspemu/PSP/GAME"):
            fldtype = "app"
        dictout.get(fldtype).append(gamename)

# Code that copies game and extras via FTP
def copy_ftp(gamename, path, system):
    filename = gamedict.get(gamename)
    ftproot = "/ux0:/"
    if system == "PSX":
        fldtype = "pspemu/PSP/GAME"
    elif system == "Vita":
        fldtype = "app"
    elif system == "PSP":
        fldtype = "pspemu/ISO"
        if os.path.isfile(os.path.join(path, fldtype, filename)):
            try:
                ftp_go(ftproot, fldtype, filename, path, gamename)
            except:
                print_out("Game", False)

    if os.path.isdir(os.path.join(path, fldtype, filename)):

        try:
            ftp_go(ftproot, fldtype, filename, path, gamename)
        except:
            print_out("Game", False)

        if values["-CB PATCH-"] == True:
            try:
                fldtype = "patch"
                ftp_go(ftproot, fldtype, filename, path, gamename)
            except:
                print_out("Patch", False)

        if values["-CB DLC-"] == True:
            try:
                fldtype = "DLC"
                ftp_go(ftproot, fldtype, filename, path, gamename)
            except:
                print_out("DLC", False)

        if values["-CB REPATCH-"] == True:
            try:
                fldtype = "repatch"
                ftp_go(ftproot, fldtype, filename, path, gamename)
            except:
                print_out("Repatch", False)

        if values["-CB READDCONT-"] == True:
            try:
                fldtype = "readdcont"
                ftp_go(ftproot, fldtype, filename, path, gamename)
            except:
                print_out("Readdcont", False)

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
def get_psp_files(folder, gamedict):
    gamedict = {}
    pspfolder = os.path.join(folder, 'pspemu', 'ISO')
    
    try:
        dirlist = os.listdir(pspfolder)
    except:
        dirlist = []
    for iso in dirlist:
        if iso.endswith(('.iso', '.ISO')):
            size = len(iso)
            isonoext = iso[:size - 4]
            gamedict[isonoext] = iso
    return list(sorted(gamedict.keys())), gamedict

def get_game_files(appfolder, tsv):
    gamedict = {}
    ciddict = {}
    try:
        dirlist = [ item for item in os.listdir(appfolder) if os.path.isdir(os.path.join(appfolder, item)) ]
    except:
        dirlist = []
    
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
    return filelist,appfolder,gamedict,ciddict

def update_cb(v, d):
    window["-CB PATCH-"].update(value=v, disabled=d)
    window["-CB REPATCH-"].update(value=v, disabled=d)
    window["-CB READDCONT-"].update(value=v, disabled=d)
    window["-CB DLC-"].update(value=v, disabled=d)
    window["-DETAILS-"].update(disabled=d)


def read_local(values, gamedict):
    folder = values["-NPS FOLDER-"]
    if values['-SYSTEM-'] == 'Vita':
        system = 'Vita'
        fileout = []
        update_cb(True, False)
        appfolder = os.path.join(folder, "app")
        tsv = 'https://nopaystation.com/tsv/PSV_GAMES.tsv'
        filelist, appfolder, gamedict, ciddict = get_game_files(appfolder, tsv)
    elif values['-SYSTEM-'] == "PSX":
        system = 'PSX'
        fileout = []
        update_cb(False, True)
        appfolder = os.path.join(folder, "pspemu", "PSP/GAME")
        tsv = 'https://nopaystation.com/tsv/PSX_GAMES.tsv'
        filelist, appfolder, gamedict, ciddict = get_game_files(appfolder, tsv)
    elif values['-SYSTEM-'] == 'PSP':
        system = 'PSP'
        fileout = []
        update_cb(False, True)
        appfolder = os.path.join(folder, "pspemu", "ISO")
        ciddict = {}
        filelist, gamedict = get_psp_files(folder, gamedict)
    
    window["-FILE LIST-"].update(filelist)
    return system, fileout, appfolder, gamedict, ciddict

def get_size(fileout, gamedict, system, appfolder):
    usedbytes = 0
    scount = 0

    for f in fileout:
        g = os.path.join(appfolder, gamedict.get(f))
        if system in ('PSX', 'Vita'):
            for path, dirs, files in os.walk(g):
                for file in files:
                    scount += 1
                    if scount % 10 == 0:
                        print(".", end="")
                    g = os.path.join(path, file)
                    usedbytes += os.path.getsize(g)
        else:
            usedbytes += os.path.getsize(g)
    return usedbytes

while True:
    event, values = window.read()
    if event in ["Exit", sg.WIN_CLOSED]:
        break

    elif event == "-MODE-":
        if values["-MODE-"] == 'FTP':
            window["-SD FOLDER-"].update("")
            window["-SD TEXT-"].update("FTP Server Address")
            window["-SD FREETEXT-"].set_size((40, None))
            window["-SD FREETEXT-"].update("FTP doesn't show Free Space")
            window["-BTN BROWSE-"].update(visible=False)
            window["-SD SIZE-"].update(visible=False)
            window["-SD FOLDER-"].set_size((30, None))
            ftpmode = True
        
        elif values["-MODE-"] == 'USB':
            window["-SD FOLDER-"].update("")
            window["-SD TEXT-"].update("SD Card on USB")
            window["-SD FREETEXT-"].update("Total space available on SD:")
            window["-SD FREETEXT-"].set_size((23, None))
            window["-BTN BROWSE-"].update(visible=True)
            window["-SD SIZE-"].update(visible=True)
            window["-SD FOLDER-"].set_size((25, None))
            ftpmode = False

    elif event == "-SYSTEM-":
        window["-SELECT LIST-"].update([])

        if values["-NPS FOLDER-"]:
            system, fileout, appfolder, gamedict, ciddict = read_local(values, gamedict)


    elif event == "-NPS FOLDER-": # Folder name was filled in, make a list of files in the folder
        system, fileout, appfolder, gamedict, ciddict = read_local(values, gamedict)


    elif event == "-SD FOLDER-": # USB Drive Selected via Browse Button
        drive = values["-SD FOLDER-"]
        freespace = get_free_space(drive)
        sdsize = format_bytes(freespace)
        window["-SD SIZE-"].update(sdsize)


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
            usedbytes = get_size(fileout, gamedict, system, appfolder)
                    
            size = format_bytes(usedbytes)
            print("\n")
            window["-SIZE-"].update(size)
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
            
            usedbytes = get_size(fileout, gamedict, system, appfolder)
            size = format_bytes(usedbytes)
            window["-SIZE-"].update(size)
            window["-SELECT LIST-"].update(fileout)

        except Exception as e:
            print(e)

    elif event == "Submit":  # Submit button was pressed
        try:
            if ftpmode is True:
                host = values["-SD FOLDER-"]
                port = 1337
                cleanup = []
                with ftputil.FTPHost(host, port,
                            session_factory=MySession) as ftp_host:
                    for f in fileout:
                        print("Copying {}:".format(f))
                        copy_ftp(f, values["-NPS FOLDER-"], system)
                        print(".")
                        cleanup.append(f)
                        window["-GAMES-"].update(gamesout)
                        window["-PATCHES-"].update(patchesout)
                        window["-DLC-"].update(dlcout)
                        window["-REPATCH-"].update(repatchout)
                        window["-READDCONT-"].update(readdcontout)
                for f in cleanup:
                    fileout.remove(f)
                usedbytes = get_size(fileout, gamedict, system, appfolder)
                size = format_bytes(usedbytes)
                window["-SIZE-"].update(size)
                window["-SELECT LIST-"].update(fileout)

            elif freespace < usedbytes:
                sg.popup_error('Not Enough Space', "Not enough space on SD Card to copy selected games.")
            elif fileout:
                cleanup = []
                for f in fileout:
                    print("Copying {}:".format(f))
                    copy_game(f, values["-NPS FOLDER-"], values["-SD FOLDER-"])
                    cleanup.append(f)
                    window["-GAMES-"].update(gamesout)
                    window["-PATCHES-"].update(patchesout)
                    window["-DLC-"].update(dlcout)
                    window["-REPATCH-"].update(repatchout)
                    window["-READDCONT-"].update(readdcontout)
                for f in cleanup:
                    fileout.remove(f)
                usedbytes = get_size(fileout, gamedict, system, appfolder)
                size = format_bytes(usedbytes)
                window["-SIZE-"].update(size)
                window["-SELECT LIST-"].update(fileout)
        except Exception as e:
            print(e)
window.close()