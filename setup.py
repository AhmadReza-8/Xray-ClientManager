import os
from enum import Enum



COMMAND = "cp"
DIR_SYSTEMD = "system/xray-mgmt.service"
DIR_SERVICE = "/etc/systemd/system"

os.system(f"{COMMAND} {DIR_SYSTEMD} {DIR_SERVICE}")

class Directories(str,Enum):
    LOG_DIR = "log"
    BANNED_DIR = f"{LOG_DIR}/banned",
    STRICKER_DIR = f"{LOG_DIR}/strickers"
    UNVALIDATED = f"{LOG_DIR}/unvalidated"



## Making program required Directory 
try:
    os.mkdir(Directories.LOG_DIR)
    print(f"{Directories.LOG_DIR} Created!!")
except FileExistsError :
    print(f"{Directories.LOG_DIR} Already Exsist")

#Creating The Sticker File
try :
    with open(Directories.STRICKER_DIR,"x") as s_f:
        print(f"{Directories.STRICKER_DIR} Created!!")
except FileExistsError :
    print(f"{Directories.STRICKER_DIR} Already Exsist")

#Creating The Banned File
try :
    with open(Directories.BANNED_DIR,"x") as b_f:
        print(f"{Directories.BANNED_DIR} Created!!")
except FileExistsError:
    print(f"{Directories.BANNED_DIR} Already Exsist")

#Creating The unvalidated File
try:
    with open(Directories.UNVALIDATED,"x") as u_f:
        print(f"{Directories.UNVALIDATED} Created!!")
except FileExistsError :
    print(f"{Directories.UNVALIDATED} Already Exsist")



