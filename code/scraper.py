"""File System Scraper
Author: Nathan Tibbetts
Date: 27 Nov. 2019
Class: ACME Volume 3

Usage: python3 scraper.py[ -p| -public][ -csv][ <user_type>]
    public: keeps the paths
    csv: will also output a csv file
    user_type: should be multi, stem, arts, or other, or 0, 1, 2, or 3 respectively.
"""

import os, stat
import numpy as np
from os.path import join, islink, exists
import pandas as pd
import pickle
from sys import platform, argv



###############################################################################
### Process Command Line Inputs

public = "-public" in argv or "-p" in argv
if public:
    try:
        argv.remove("-public")
    except:
        argv.remove("-p")
csv = "-csv" in argv
if csv: argv.remove("-csv")
if len(argv) > 1:
    user_type = argv[1]
    assert user_type in ["0", "1", "2", "3", "multi", "stem", "acme", "arts", "other"], "Invalid user type"
else: user_type = None


###############################################################################
### Initialization and Function Definitions

stats = [] # to contain tuples (path, stat_obj)
paths = [] # to contain paths found, for: index -> path
paths_dict = {} # path -> index
data = []

failed = []
failed2 = []
failed_links = []

stat_labels = [
    "Index", "Parent", "Inode",                                         # Indices 0-2
    "Device", "User ID", "Group ID", "Size", "Hidden", "Sub-Hidden",    # Indices 3-8
    "Access Time", "Modify Time", "Metachange Time",                    # Indices 9-11
    "Sticky", "User Read", "User Write", "User Execute",                # Indices 12-15
    "Group Read", "Group Write", "Group Execute",                       # Indices 16-20
    "Other Read", "Other Write", "Other Execute",                       # Indices 19-21
    "Is Directory", "Is Regular File", "Is Link To",                    # Indices 22-24
    "Desktop", "Sub-Desktop", "Sub-Desktop-Parent"]                     # Indices 25-27

# Helper Functions
def hidden(p, s):
    """ Figures out if a file/dir is hidden or not.
        Returns: (bool)
    """
    if windows:
        return s.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN
    name = "/".join(p.split("/")[-2]) if p[-1] == "/" else "/".join(p.split("/")[-1])
    return name[0] == "." if name else False

def get_link(p, s, failed_links, parent_path):
    """ Gets the index pointed to by a link.
        Returns: (int) index if valid, -1 if not a link, -2 if broken link
            or if we couldn't figure it out.
    """
    if not islink(p): return -1
    l = ""
    try:
        l = os.readlink(p)
        
        # Relative paths
        parts = l.split("/")
        parent_parts = parent_path.split("/")[:-1]
        if (windows and parts[0] == top[:2]) or (not windows and parts[0]):
            new_path = parent_parts + parts
            while "." in new_path: new_path.remove('.') # TODO: speedup
            while ".." in new_path: # TODO: speedup
                i = new_path.index("..")
                new_path.remove(i-1)
                new_path.remove(i-1)
            l = "/".join(new_path)
            
        # Resolve the link to an index if possible
        if (l + "/") in paths_dict: link = paths_dict[l + "/"]
        elif l in paths_dict: link = paths_dict[l]
        else:
            link = -2
    except:
        link = -2
    if link == -2: failed_links.append((p, l))
    return link


###############################################################################
### Grab a few data on the OS and environment

if user_type is None:
    user_type = input("""Please input the user type:
    0: Multiple Users
    1: STEM Major/Professional
    2: Arts Major/Professional
    3: Personal Computer or Other\n""")# stem, multi, arts, other
user_type = {"0": "multi", "1": "stem", "2": "arts", "3":"other",
    "multi": "multi", "acme": "stem", "stem": "stem", "arts": "arts", "other": "other"}[user_type]
windows = os.name == "nt"

# Set the path to start from
top = "C:/" if windows else '/'


###############################################################################
### Get the stats and paths for the OS

# Recursively walk through the file system tree
stats.append((top, os.stat(top, follow_symlinks=False)))
paths_dict[top] = 0
paths.append(top)
for root, dirs, files in os.walk(top):
    
    # Scrape directory info
    for name in dirs:
        path = join(root,name) + "/"
        try:
            stats.append((path, os.stat(path, follow_symlinks=False)))
            if path not in paths_dict:
                paths_dict[path] = len(paths)
                paths.append(path)
        except:
            failed.append(path)
                
    # Scrape file info
    for name in files:
        path = join(root,name)
        try:
            stats.append((path, os.stat(path, follow_symlinks=False)))
            if path not in paths_dict:
                paths_dict[path] = len(paths)
                paths.append(path)
        except:
            failed.append(path)
            
    # Progress
    if len(paths) % 50000 == 0: print(len(paths), end='\r')
print(len(paths))


###############################################################################
### Compile specific data from the stat objects

# Get the specific stats and put them together
for p, s in stats:
    try:
        parent_path = p[:p.rfind("/")+1] if p[-1] != "/" else p[:p[:-1].rfind("/")+1]
        parent = paths_dict[parent_path] if p != top else -1
        data.append([
            paths_dict[p], parent, s.st_ino,
            s.st_dev, s.st_uid, s.st_gid, s.st_size, hidden(p, s), False,
            s.st_atime_ns, s.st_mtime_ns, s.st_ctime_ns,
            bool(s.st_mode & stat.S_ISVTX), bool(s.st_mode & stat.S_IRUSR), bool(s.st_mode & stat.S_IWUSR), bool(s.st_mode & stat.S_IXUSR),
            bool(s.st_mode & stat.S_IRGRP), bool(s.st_mode & stat.S_IWGRP), bool(s.st_mode & stat.S_IXGRP),
            bool(s.st_mode & stat.S_IROTH), bool(s.st_mode & stat.S_IWOTH), bool(s.st_mode & stat.S_IXOTH),
            stat.S_ISDIR(s.st_mode), stat.S_ISREG(s.st_mode), get_link(p, s, failed_links, parent_path)
        ])
    except:
        failed2.append(p)
        
    # Progress
    if len(data) % 50000 == 0: print(len(data), end='\r')
print(len(data))
        
# Fill in Sub-Hidden. These depend on them being correctly in a valid downward hierarchical ordering!
H = stat_labels.index("Hidden")
SH = stat_labels.index("Sub-Hidden")
P = stat_labels.index("Parent")
data[0][SH] = data[0][H]
for row in data[1:]:
    row[SH] = row[H] or data[row[P]][SH]

# Obfuscate but keep info about Destkop folders
D = stat_labels.index("Desktop") # Column True if Actual "Desktop" folder
SD = stat_labels.index("Sub-Desktop") # Column True if Desktop folder or Descendant
SDP = stat_labels.index("Sub-Desktop-Parent") # Column True if Parent of Desktop or descendant thereof
for row in data:
    row += [False, False, False]
    parts = paths[row[0]].split("/")
    if not parts[-1]: parts = parts[:-1]
    if parts[-1] == "Desktop": # Is a desktop folder itself
        row[D] = True # Desktop
        row[SD] = True # Sub-Desktop
        if row[P] >= 0:
            data[row[P]][SDP] = True # Desktop-Parent
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

