import pickle
import os


# -----------------------------------------------------------------------------
def saveAsPickled(filename, data):
    with open(filename, mode='wb') as file:
        pickle.dump(data, file)


# -----------------------------------------------------------------------------
def loadPickled(filename):
    if os.path.isfile(filename):
        with open(filename, mode='rb') as file:
            return pickle.load(file)
    else:
        return None

