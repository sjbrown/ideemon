#! /usr/bin/python

# autotest: doctest

# TODO: I should investigate using gevent to run subprocesses
#       in a concurrent manner

import os
import sys
import time
import pyinotify

compatibleVersions = [(1,0)]
watchPluginsDir = os.path.join(os.path.dirname(__file__), 'watch_plugins')
testPluginsDir = os.path.join(os.path.dirname(__file__), 'test_plugins')
notifyPluginsDir = os.path.join(os.path.dirname(__file__), 'notify_plugins')

# -----------------------------------------------------------------------------
def getPluginFilePaths(dirPath):
    fileList = os.listdir(dirPath)
    pluginFileNames = [fname for fname in fileList
                       if (not fname.startswith('_')
                           and fname.endswith('.py'))]
    pluginFilePaths = [os.path.join(dirPath, fname)
                       for fname in pluginFileNames]
    return pluginFilePaths

# -----------------------------------------------------------------------------
def getPluginModules(dirPath):
    pluginModules = []
    origPath = sys.path
    sys.path.insert(0, dirPath) #insert, not append: users can override std modules
    for fpath in getPluginFilePaths(dirPath):
        dirName = os.path.dirname(fpath)
        baseName = os.path.basename(fpath)
        modName = baseName.rsplit('.py', 1)[0]
        module = __import__(modName, globals(), locals(), level=0)
        if (hasattr(module, 'pluginVersion')
            and module.pluginVersion in compatibleVersions):
            pluginModules.append(module)
        else:
            print ('Could not load plugin module %s' % str(module))
    sys.path = origPath
    return pluginModules

# -----------------------------------------------------------------------------
def getAllDirectories():
    allDirs = []
    for module in getPluginModules(watchPluginsDir):
        allDirs += module.directoriesToWatch()
    return allDirs

# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
def findTestsFor(fpath):
    '''
    >>> findTestsFor('/dev/null')
    []
    '''
    allTests = []
    if ignoreFilter(fpath):
        return allTests
    for module in getPluginModules(testPluginsDir):
        allTests += module.findTestsFor(fpath)
    return allTests

# -----------------------------------------------------------------------------
def output(*args):
    msg = ' '.join([str(x) for x in args])
    sys.stdout.write( msg + '\n' )

def notify(fpath, lineNum, summary):
    output(' * NOTIFY', fpath, lineNum, summary)
    output(' *')
    for module in getPluginModules(notifyPluginsDir):
        module.notify(fpath, lineNum, summary)
    
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
def test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    main()
    #test()
