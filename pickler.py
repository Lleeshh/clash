import pickle
import os


# -----------------------------------------------------------------------------
def saveAsPickled(filename, data):
    with open(filename, mode='wb') as f:
        pickle.dump(data, f)


# -----------------------------------------------------------------------------
def loadPickled(filename):
    if os.path.isfile(filename):
        with open(filename, 'rb') as pickleFile:
            return pickle.load(pickleFile)
    else:
        return None

