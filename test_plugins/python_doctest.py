#! /usr/bin/python

# autotest: doctest

import os
import re
import sys
import doctest
import subprocess

pluginVersion = (1,0)

def log_error(*args):
    msg = ' '.join([str(x) for x in args]) + '\n'
    sys.stderr.write(msg)

# pattern to match lines like: # autotest: doctest
prefix = r'^\s*#\s*autotest\s*:\s*'
simpleDoctestPattern = re.compile(prefix + r'doctest\s*$',
                                  re.IGNORECASE)
# pattern to match lines like: # autotest: doctest.testfile:test/foo.doctest
testfilePattern = re.compile(prefix + r'doctest\.testfile\s*:(.*)',
                                  re.IGNORECASE)

doctestErrorPattern = re.compile(r'^File .*line (\d+),')


def doctestFn(*args, **kwargs):
    '''run doctest.testmod on the module
    If there are no errors, return None
    If there are errors, return a list of (filepath, lineNumber, errorSummary)
    '''

    #doctest is run in a subprocess for isolation.
    fpath = args[0]
    cmd = 'python -m doctest %s' % fpath

    p = subprocess.Popen(cmd, shell=True,
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         )

    output = p.stdout.read(100*1024) # read 100KiB
    print output
    errors = []
    for line in output.splitlines():
        m = doctestErrorPattern.search(line)
        if m:
            lineNum = m.group(1)
            errors.append((fpath, lineNum, 'doctest failed'))
            break

    return errors

def testfileFn(srcPath, testPath, **kwargs):
    '''run doctest.testfile on the testfile
    If there are no errors, return None
    If there are errors, return a list of (filepath, lineNumber, errorSummary)
    '''

    #doctest is run in a subprocess for isolation.
    srcDirname = os.path.dirname(srcPath)
    script = ('import doctest'
              ';import sys'
              ';sys.path.append("%s")'
              ';doctest.testfile("%s", module_relative=False)'
             ) % (srcDirname, testPath)

    cmd = 'python', '-c', script
    print 'cmd', cmd

    p = subprocess.Popen(cmd, shell=True,
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         )

    print '       NO OUTPUT YET'
    p.communicate()
    print '       NO OUTPUT YET'
    output = p.stdout.read(100*1024) # read 100KiB
    print 'output:\n', output
    errors = []
    for line in output.splitlines():
        m = doctestErrorPattern.search(line)
        if m:
            lineNum = m.group(1)
            errors.append((fpath, lineNum, 'testfile doctest failed'))
            break

    return errors


def findTestsFor(fpath):
    '''Find tests for python files. Returns a doctest test if the
    file has a comment line that looks like "# autotest: doctest"

    >>> findTestsFor('/dev/null')
    []
    '''
    try:
        fileSize = os.path.getsize(fpath)
    except OSError, ex:
        log_error('could not get file size', fpath, ex)
        return []
    if fileSize > 100*1024: #bigger than 100KiB
        log_error('file too big', fpath)
        return []
    try:
        fp = file(fpath)
    except Exception, ex:
        log_error('could not open', fpath, ex)
        return []
    contents = fp.read()
    fp.close()
    lines = contents.splitlines()
    if not lines:
        log_error('empty file', fpath)
        return []

    firstline = lines[0]

    if not (fpath.endswith('.py')
        or (firstline.startswith('#!') and 'python' in firstline)):
        return []

    #tests = findDoctestsFor(lines) + findTestfileTestsFor(fpath, lines)
    tests = findTestfileTestsFor(fpath, lines)
    return tests

def findDoctestsFor(lines):
    '''Returns a doctest test if the file has a comment line that
    looks like "# autotest: doctest"

    >>> findDoctestsFor('/dev/null')
    []
    '''
    tests = []

    for line in lines:
        if simpleDoctestPattern.search(line):
            print 'found doctest pattern', line
            #            function    args     kwargs
            tests.append((doctestFn, (fpath,), dict()))
            break

    return tests

def findTestfileTestsFor(fpath, lines):
    '''Returns a doctest test if the file has a comment line that
    looks like "# autotest: doctest.testfile:test/foo.doctest"

    >>> findTestfileTestsFor('/dev/null')
    []
    '''
    tests = []

    for line in lines:
        match = testfilePattern.search(line)
        if match:
            relativeTestPath = match.group(1).strip()
            srcDirname = os.path.dirname(fpath)
            testPath = os.path.join(srcDirname, relativeTestPath)

            print 'found testfile pattern', line
            #            function     args              kwargs
            tests.append((testfileFn, (fpath,testPath), dict()))
            break

    return tests


def main():
    os_py = os.__file__.replace('pyc', 'py')
    print os_py
    for t in findTestsFor(os_py):
        print t

    thismodule_py = __file__.replace('pyc', 'py')
    print thismodule_py
    for t in findTestsFor(thismodule_py):
        print t

if __name__ == '__main__':
    main()
