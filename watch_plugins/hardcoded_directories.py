#! /usr/bin/env python

import os
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

pluginVersion = (1,0)

hardcoded_list = '''\
/a/work/catan
'''

def directoriesToWatch():
    hlist = hardcoded_list.strip()
    hlist = hlist.split('\n')
    dirs = []
    for l in hlist:
        d = l.strip()
        if os.path.isdir(d):
            dirs.append(d)
        else:
            log.warn('Directory "%s" does not exist' % d)
    return dirs

def main():
    for d in directoriesToWatch():
        print d

if __name__ == '__main__':
    main()
