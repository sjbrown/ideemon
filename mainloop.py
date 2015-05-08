#! /usr/bin/python

# autotest: doctest

# TODO: I should investigate using gevent to run subprocesses
#       in a concurrent manner

import os
import sys
import time
import pyinotify
import collections
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

INTERVAL_SECS = 6

compatibleVersions = [(1,0)]
THIS_DIR = os.path.dirname(__file__)
testPluginsDir = os.path.join(THIS_DIR, 'test_plugins')
watchPluginsDir = os.path.join(THIS_DIR, 'watch_plugins')
notifyPluginsDir = os.path.join(THIS_DIR, 'notify_plugins')
environment_plugins_dir = os.path.join(THIS_DIR, 'environment_plugins')

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
    # insert, not append: users can override std modules
    sys.path.insert(0, dirPath)
    for fpath in getPluginFilePaths(dirPath):
        dirName = os.path.dirname(fpath)
        baseName = os.path.basename(fpath)
        modName = baseName.rsplit('.py', 1)[0]
        module = __import__(modName, globals(), locals(), level=0)
        if (hasattr(module, '__plugin_version')
            and module.__plugin_version in compatibleVersions):
            pluginModules.append(module)
        else:
            log.error('Could not load plugin module %s' % str(module))
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
def find_tests_for(fpath):
    '''
    >>> find_tests_for('/dev/null')
    []
    '''
    allTests = []
    if ignoreFilter(fpath):
        return allTests
    for module in getPluginModules(testPluginsDir):
        allTests += module.find_tests_for(fpath)
        log.info(' -#- got test spec from %s', module)
    return allTests

# -----------------------------------------------------------------------------
def output(*args):
    msg = ' '.join([str(x) for x in args])
    sys.stdout.write( msg + '\n' )

def notify(errors):
    for module in getPluginModules(notifyPluginsDir):
        if hasattr(module, 'new_error_set'):
            module.new_error_set()
    for error in errors:
        fpath, lineNum, summary = error
        output(' * NOTIFY', fpath, lineNum, summary)
        output(' *')
        for module in getPluginModules(notifyPluginsDir):
            module.notify(fpath, lineNum, summary)

# -----------------------------------------------------------------------------
class Accountant:
    filesProcessed = collections.defaultdict(lambda: 0)
    lastTouch = collections.defaultdict(lambda: 0)

    @classmethod
    def filterDirs(cls, oldDirs, newDirs):
        '''Filter out directories that are too expensive.
        Right now that means:
        - any directory that had more than 10 changed files last iteration
        - any directory that hasn't seen action in over a minute
        '''
        dirlist = []
        for d in set(newDirs).difference(oldDirs):
            cls.lastTouch[d] = 0
            dirlist.append(d)
        for d in set(oldDirs):
            if cls.filesProcessed[d] > 10:
                log.warn('directory '+ d +' is too busy')
                continue
            cls.lastTouch[d] += 1
            if cls.lastTouch[d] > 60/INTERVAL_SECS:
                log.info('directory '+ d+ ' older than 60 secs')
                continue
            dirlist.append(d)
        cls.filesProcessed.clear()
        return dirlist

# -----------------------------------------------------------------------------
def find_environment_for(test_spec):
    # default to subprocess environment for isolation
    env_spec = test_spec.get('env', 'subprocess')
    all_envs = []
    for module in getPluginModules(environment_plugins_dir):
        found = module.find_environment(env_spec)
        if found:
            all_envs.append(found)
    if len(all_envs) > 1:
        log.error('MORE THAN ONE ENVIRONMENT FOUND %s', all_envs)
    return all_envs[0]

# -----------------------------------------------------------------------------
class EventProcessor(pyinotify.ProcessEvent):
    def process_default(self, event):
        pass #silence output
    def process_IN_MODIFY(self, event):
        log.info(' -#- EVENT: %s', event)

        dirName = os.path.dirname(event.pathname)
        Accountant.filesProcessed[dirName] += 1

        for test_spec in find_tests_for(event.pathname):
            environment = find_environment_for(test_spec)
            testFn = test_spec['make_cmd_fn']

            testArgs = test_spec.get('args', ())

            testKwargs = test_spec.get('kwargs', {})

            report_fn = test_spec.get('report_fn',
                                     lambda x,y: ['report: ' + x[:50] + '...'])
            try:
                with environment() as env:
                    output, errput = env.run(testFn, *testArgs, **testKwargs)
                    report = report_fn(output, errput)
                    notify(report)
            except Exception, ex:
                print 'FAIL'
                print ex

# -----------------------------------------------------------------------------
def safeloop(wm, notifier):
    notifier.start()
    watched_dirs = {}
    try:
        while True:
            new_dirs = getAllDirectories()
            new_dirs = Accountant.filterDirs(watched_dirs.keys(), new_dirs)
            for d in new_dirs:
                if d in watched_dirs:
                    continue
                log.info('adding '+ d)
                retval =  wm.add_watch(d, pyinotify.ALL_EVENTS)
                watched_dirs.update(retval)
            log.info('watched dirs: ' + str(watched_dirs))
            time.sleep(INTERVAL_SECS)
            for k, v in watched_dirs.items():
                if k not in new_dirs:
                    wm.rm_watch(v)
                    del watched_dirs[k]

    finally:
        # destroy the inotify's instance on this interrupt (stop monitoring)
        notifier.stop()

# -----------------------------------------------------------------------------
#watchedDirs = []
#def loopCB(notifier):
    #wm = notifier._watch_manager
    #dirsThisIteration = getAllDirectories()
    #for d in dirsThisIteration:
        #if d in watchedDirs:
            #continue
        #print 'adding', d
        #wm.add_watch(d, pyinotify.ALL_EVENTS)
        #watchedDirs.append(d)
    #print watchedDirs
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
