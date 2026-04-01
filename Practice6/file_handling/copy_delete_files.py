import shutil
import os
shutil.copy("data.txt", "copy_data.txt")
if os.path.exists("copy_data.txt"):
    os.remove("copy_data.txt")
