"""Repairer for Scraped File System Data in the data subfolder
Author: Nathan Tibbetts
Date: 27 Nov. 2019
Class: ACME Volume 3

Usage: python3 data_repair.py
"""

import numpy as np
import pandas as pd
import os
from sys import argv


# OLD:
# Fix sub-hidden bug; relies on os hierarchy
#data = a.values
# for i, row in enumerate(data):
#     if data[row[0]][6] or data[row[0]][7]:
#         a.set_value("Sub-Hidden", i, True)
#for row in data:
#    if row[6]: assert(row[7])
#    if data[row[0]][7]: assert(row[7])
        
# for d in l:
#     a = pd.read_pickle(d)
#     v = a.values
#     for i, row in enumerate(v):
#         if row[6] or v[row[0]][7]: a.set_value("Sub-Hidden", i, True)
#     a.to_pickle(d)
#     print(d)


###############################################################################
### Initialization and Setup

files = [argv[1]] if os.path.isfile(argv[1]) and argv[1][-4:] == ".pkl" else [f for f in os.listdir(argv[1]) if os.path.isfile(f) and f[-4:] == ".pkl"]


###############################################################################
### Iterate to build new/replacement columns

for f in files:

    # Open the file and check if we need to fix it
    df = pd.read_pickle(f)
    if "Sub-Desktop-Parent" in df:
        del(df) # Cleanup
        continue

    # Initialization
    sub_hidden = []
    sub_desktop = []
    sub_desktop_parent = []

    # Fill in Sub-Hidden. These depend on them being correctly in a valid downward hierarchical ordering!
    sub_hidden.append(df.Hidden[0])
    for i in range(1, len(df)):
        sub_hidden.append(df.Hidden[i] or df.at("Sub-Hidden", df.Parent[i]))

    # Fix Desktop etc. info
    for i in range(len(df)):
        row += [False, False, False]
        parts = paths[row[0]].split("/")
        if not parts[-1]: parts = parts[:-1]
        if parts[-1] == "Desktop": # Is a desktop folder itself
            row[D] = True # Desktop
            row[SD] = True # Sub-Desktop
            if row[P] >= 0: data[row[P]][SDP] = True # Desktop-Parent
        elif "Desktop" in parts:
            row[SD] = True
    for row in data: # This also depends on downward hierarchical ordering
        if row[P] >= 0 and data[row[P]][SDP]:
            row[SDP] = True


    ###############################################################################
    ### Data Formatting and Saving

    # Put it into a Pandas DataFrame
    df = pd.DataFrame(data, columns=stat_labels)
    ind = df.Index
    df.drop("Index", axis=1, inplace=True)
    df.index = ind
    if public: df["Path"] = paths

    # Save it to disk
    i = 0
    prefix = f"./{platform}_{user_type}_filesystem"
    suffix = "_public" if public else ""
    file_name = prefix + str(i) + suffix
    while exists(file_name + ".pkl"): i += 1
    df.to_pickle(file_name + ".pkl")

    # Optionally produce CSV
    if csv:
        df.to_csv(file_name + ".csv")

    del(df) # Cleanup to avoid filling RAM and crashing

