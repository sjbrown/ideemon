#! /usr/bin/python

import os

pluginVersion = (1,0)

hardcoded_list = '''\
/a/work/catan
'''

def directoriesToWatch():
    l = hardcoded_list.strip()
    l = l.split('\n')
    dirs = []
    for l in l:
        d = l.strip()
        if os.path.isdir(d):
            dirs.append(d)
        else:
            print 'Directory "%s" does not exist' % d
    return dirs

def main():
    for d in directoriesToWatch():
        print d

if __name__ == '__main__':
    main()
