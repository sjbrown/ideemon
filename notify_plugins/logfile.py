#! /usr/bin/python

__plugin_version = (1,0)

def notify(fpath, lineNum, summary):

    fp = file('/tmp/watcher.log', 'a')
    fp.write( 'LINE %s    %s\n' % (lineNum, fpath) )
    fp.write( '%s\n' % summary )
    fp.close()
