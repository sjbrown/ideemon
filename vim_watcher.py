#! /usr/bin/python

import os
import subprocess


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
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         )

    for line in p.stdout:
        line = line.strip()
        if line.endswith('.swp'):
            swp_fpath = line.rsplit(' ', 1)[1]
            fpath = swp_fpath.rsplit('.swp')[0]
            head, tail = fpath.rsplit('/', 1)
            tail = tail.split('.', 1)[1]
            fpath = head +'/'+ tail
            yield fpath

def directoriesToWatch():
    directories = set()
    for fpath in allFilesOpenedByVi():
        directories.add( os.path.dirname(fpath) )
    return list(directories)

def main():
    for f in allFilesOpenedByVi():
        print f


if __name__ == '__main__':
    main()
