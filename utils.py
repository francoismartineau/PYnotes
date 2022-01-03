import os
import psutil
import ahk
#pip install ahk

def get_script_dir_file_path(name):
    script_path = os.path.realpath(__file__)
    script_folder = os.path.dirname(script_path)
    return os.path.join(script_folder, name)    

def get_lock_file_path():
    return get_script_dir_file_path("PY_is_running.pid")

def lock_script():
    lock_file_path = get_lock_file_path()
    f = open(lock_file_path, "w")
    f.write(str(os.getpid()))
    f.close()
    print("locked script")

def unlock_script():
    lock_file_path = get_lock_file_path()
    os.remove(lock_file_path)
    print("unlocked script")

def already_running():
    res = False
    lock_file_path = get_lock_file_path()
    if os.path.isfile(lock_file_path):
        with open(lock_file_path, 'r') as f:
            pid = f.read()
        if pid.isnumeric() and psutil.pid_exists(int(pid)):
            res = True
        else:
            unlock_script()
            res = False
    return res

def still_locked():
    res = already_running()
    if (not res):
        print("PY was unlocked by an external process")
    return res

def fl_ahk_running():
    title = "FLahkIsRunningWindow"
    id = ahk.AHK().win_get(title=title).id
    res = id != ""
    if (not res):
        print("FLahk is not running.")
    return res
