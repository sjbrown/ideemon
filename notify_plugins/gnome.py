#! /usr/bin/python

pluginVersion = (1,0)

import os
import pynotify

COUNT = 0

seen_errors = {}

def new_error_set():
    global COUNT
    COUNT = 0

def notify(fpath, lineNum, summary):
    key = (fpath, lineNum, summary)
    errCount = seen_errors.get(key, 0)
    seen_errors[key] = errCount + 1

    if seen_errors[key] > 5:
        # we have seen this error 5 times already
        return

    # only show a maximum of 5 errors
    global COUNT
    COUNT += 1
    if COUNT > 5:
        return

    basename = os.path.basename(fpath)
    title = 'LINE %s  %s' % (lineNum, basename)
    msg = '%s\n' % summary

    pynotify.init(title)
    notification = pynotify.Notification( title, msg )
    notification.show()
