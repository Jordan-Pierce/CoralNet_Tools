import os
import sys
import datetime


# ------------------------------------------------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------------------------------------------------

# Get the current script's directory (where init_project.py is located)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add the parent directory (Project) to the Python path
PROJECT_DIR = os.path.dirname(script_dir)
sys.path.append(PROJECT_DIR)

# Make the Data directory
DATA_DIR = f"{os.path.dirname(PROJECT_DIR)}\\Data"
os.makedirs(DATA_DIR, exist_ok=True)

# Make the Cache directory
CACHE_DIR = f"{DATA_DIR}\\Cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Patch extractor path
PATCH_EXTRACTOR = f'{PROJECT_DIR}\\Tools\\Patch_Extractor\\CNNDataExtractor.exe'

# For all the logging
LOG_PATH = f"{DATA_DIR}\\Cache\\logs.log"

# MIR specific, mapping path
MIR_MAPPING = f'{DATA_DIR}\\Mission_Iconic_Reefs\\MIR_VPI_CoralNet_Mapping.csv'

# Coralnet labelset file for dropdown menu in gooey
CORALNET_LABELSET_FILE = f"{CACHE_DIR}\\CoralNet_Labelset_List.csv"

# Constant for the CoralNet url
CORALNET_URL = "https://coralnet.ucsd.edu"

# CoralNet Source page, lists all sources
CORALNET_SOURCE_URL = CORALNET_URL + "/source/about/"

# CoralNet Labelset page, lists all labelsets
CORALNET_LABELSET_URL = CORALNET_URL + "/label/list/"

# URL of the login page
LOGIN_URL = "https://coralnet.ucsd.edu/accounts/login/"

# CoralNet functional groups
FUNC_GROUPS_LIST = [
    "Other Invertebrates",
    "Hard coral",
    "Soft Substrate",
    "Hard Substrate",
    "Other",
    "Algae",
    "Seagrass"]

# Mapping from group to ID
FUNC_GROUPS_DICT = {
    "Other Invertebrates": "14",
    "Hard coral": "10",
    "Soft Substrate": "15",
    "Hard Substrate": "16",
    "Other": "18",
    "Algae": "19",
    "Seagrass": "20"}

# Image Formats
IMG_FORMATS = ["jpg", "jpeg", "png", "bmp"]


# ------------------------------------------------------------------------------------------------------------------
# Functions
# ------------------------------------------------------------------------------------------------------------------

def get_now():
    """
    Returns a timestamp; used for file and folder names
    """
    # Get the current datetime
    now = datetime.datetime.now()
    now = now.strftime("%Y-%m-%d_%H-%M-%S")

    return now


def print_sfm_progress(p):
    """

    """

    print("progress: {}/{}".format(int(p), 100))