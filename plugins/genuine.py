from util import hook
from subprocess import check_output
import os;

@hook.command(autohelp=False)
def genuine(inp, say=None):
    ".genuine -- gets whether or not you're stealing windows you jerk"

    if ("nt" != os.name):
        say("this box isn't even windows!")
        return

    output = check_output("cscript %WINDIR%\System32\slmgr.vbs /dli", shell=True)

    if "License Status: Licensed" in "".join(output.decode("ascii")):
        say("they stopped freeloading!  yay")
    else:
        say("whoever runs this server is a terrible person who stole windows")
