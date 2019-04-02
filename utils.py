import argparse
import datetime
import os
import sys
import time


# -----------------------------------------------------------------------------
# Hack to get the paths to work on windows to find any input or output files
def addSubDirsToPath():
    excludeList = ['.git', '.idea', 'venv', '__pycache__', 'output']
    a_dir = os.path.dirname(sys.modules['__main__'].__file__)
    if a_dir is None:
        return

    for name in os.listdir(a_dir):
        if os.path.isdir(name):
            pathToAdd = a_dir + "\\" + name
            if name not in excludeList:
                sys.path.append(pathToAdd)


# -----------------------------------------------------------------------------
def str2bool(v):
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


# -----------------------------------------------------------------------------
def getDaysFromNow(timeStamp):
    if timeStamp > 0:
        providedTime = datetime.datetime.fromtimestamp(timeStamp)
        todayDateTime = datetime.datetime.fromtimestamp(time.time())
        diff = todayDateTime - providedTime
        return diff.days

    return None


# -----------------------------------------------------------------------------
def openBrowserTab(url):
    import webbrowser
    webbrowser.open(url, new=2)
