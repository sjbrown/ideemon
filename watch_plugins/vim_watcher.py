#! /usr/bin/python

import os
import subprocess
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

__plugin_version = (1,0)

def allFilesOpenedByVi():
    username = os.environ['USER']
    args = (
    ' -a' # AND the following options
    ' -b' # don't do any kernel blocking operations
    ' -n' # don't do any hostname lookups
    #' -N' # include NFS directories
    ' -u %s' #only do user %s
    ) % username
    cmd = 'lsof' + args

    p = subprocess.Popen(cmd, shell=True,
                         stdout=subprocess.PIPE,
                         stderr=open('/dev/null', 'w'),
                         )

    for line in p.stdout:
        line = line.strip()
        if '.swp' in line:
            try:
                # At this point, line looks like "vi  1234  username  1 REG  /foo/bar/.baz.py.swp"
                fpath = line.rsplit('.swp')[0] # "vi  1234  username  1 REG  /foo/bar/.baz.py"
                fpath = '/' + fpath.split('/', 1)[1] #                      "/foo/bar/.baz.py"
                head, tail = fpath.rsplit('/', 1)    #                      "/foo/bar", ".baz.py"
                tail = tail.split('.', 1)[1]         #                      "/foo/bar", "baz.py"
                fpath = head +'/'+ tail              #                      "/foo/bar/baz.py"
                yield fpath
            except Exception, ex:
                log.error(str(ex))

def directoriesToWatch():
    directories = set()
    for fpath in allFilesOpenedByVi():
        directories.add( os.path.dirname(fpath) )
    log.info('Directories watched from vim: %s' % directories)
    return list(directories)

def main():
    for f in allFilesOpenedByVi():
        print f


if __name__ == '__main__':
    main()
