from util import hook
from subprocess import check_output

@hook.command(autohelp=False)
def genuine(inp, say=None):
    ".genuine -- gets whether or not you're stealing windows you jerk"

    output = check_output("cscript %WINDIR%\System32\slmgr.vbs /dli", shell=True)

    if "License Status: Licensed" in "\n".join(output):
        say("they stopped freeloading!  yay")
    else:
        say("whoever runs this server is a terrible person who stole windows")