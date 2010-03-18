#! /usr/bin/python

pluginVersion = (1,0)

import os
import pynotify

def notify(fpath, lineNum, summary):

    basename = os.path.basename(fpath)
    title = 'LINE %s  %s' % (lineNum, basename)
    msg = '%s\n' % summary

    pynotify.init(title)
    notification = pynotify.Notification( title, msg )
    notification.show()
