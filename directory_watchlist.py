#! /usr/bin/python

# autotest: doctest

# TODO: I should investigate using gevent to run subprocesses
#       in a concurrent manner

import os
import sys
import time
import pyinotify

def getAllDirectories():
    # TODO implement a plugin system
    import vim_watcher
    import directory_list
    allDirs = []
    for module in [vim_watcher, directory_list]:
        allDirs += module.directoriesToWatch()
    return allDirs

def ignoreFilter(fpath):
    '''
    >>> ignoreFilter('foo.py')
    False
    >>> ignoreFilter('foo.py.swp')
    True
    '''
    if fpath.endswith('.swp'):
        return True
    else:
        return False

def findTestsFor(fpath):
    '''
    >>> findTestsFor('/dev/null')
    []
    '''
    # TODO implement a plugin system
    import python_testfinder
    allTests = []
    if ignoreFilter(fpath):
        return allTests
    for module in [python_testfinder]:
        allTests += module.findTestsFor(fpath)
    return allTests

def output(*args):
    msg = ' '.join([str(x) for x in args])
    sys.stdout.write( msg + '\n' )

def notify(fpath, lineNum, summary):
    output(' * NOTIFY', fpath, lineNum, summary)
    output(' *')
    
class EventProcessor(pyinotify.ProcessEvent):
    def process_default(self, event):
        pass #silence output
    def process_IN_MODIFY(self, event):
        tests = findTestsFor(event.pathname)
        for testTuple in tests:
            testFn = testTuple[0]
            if len(testTuple) > 1:
                testArgs = testTuple[1]
            else:
                testArgs = ()
            if len(testTuple) > 2:
                testKwargs = testTuple[2]
            else:
                testKwargs = {}
            try:
                errors = testFn(*testArgs, **testKwargs)
                for error in errors:
                    fpath, lineNum, summary = error
                    notify(fpath, lineNum, summary)
            except Exception, ex:
                print 'FAIL'
                print ex

def safeloop(wm, notifier):
    notifier.start()
    watchedDirs = []
    try:
        while True:
            dirsThisIteration = getAllDirectories()
            for d in dirsThisIteration:
                if d in watchedDirs:
                    continue
                print 'adding', d
                wm.add_watch(d, pyinotify.ALL_EVENTS)
                watchedDirs.append(d)
            print watchedDirs
            time.sleep(5)

    finally:
        # destroy the inotify's instance on this interrupt (stop monitoring)
        notifier.stop()

watchedDirs = []
def loopCB(notifier):
    wm = notifier._watch_manager
    dirsThisIteration = getAllDirectories()
    for d in dirsThisIteration:
        if d in watchedDirs:
            continue
        print 'adding', d
        wm.add_watch(d, pyinotify.ALL_EVENTS)
        watchedDirs.append(d)
    print watchedDirs
    #time.sleep(5)

def main():
    wm = pyinotify.WatchManager()
    processor = EventProcessor()
    notifier = pyinotify.ThreadedNotifier(wm, processor)
    safeloop(wm, notifier)
    #notifier = pyinotify.Notifier(wm, processor)
    #loopCB(notifier)
    #notifier.loop(daemonize=True, callback=loopCB,
    #notifier.loop(callback=loopCB,
                  #force_kill=True, stdout='/tmp/stdout.txt')

def test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    main()
    #test()
