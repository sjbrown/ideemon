#! /usr/bin/python

# autotest: doctest
# autotest: unittest.testfile:tests/test_python_unittest.py

import os
import re
import sys
import subprocess

pluginVersion = (1,0)

def log_error(*args):
    msg = ' '.join([str(x) for x in args]) + '\n'
    sys.stderr.write(msg)

prefix = r'^\s*#\s*autotest\s*:\s*'

# pattern to match lines like: # autotest: unittest.testfile:tests/test_me.py
testfilePattern = re.compile(prefix + r'unittest\.testfile\s*:(.*)',
                             re.IGNORECASE)
testfileShortPattern = re.compile(prefix + r'unittest')

unittestErrorPattern = re.compile('File .*/([^/]+\.py)", line (\d+)')


def testfileFn(srcPath, testPath, **kwargs):
    '''run the unittest file
    If there are no errors, return None
    If there are errors, return a list of (filepath, lineNumber, errorSummary)
    '''

    #run in a subprocess for isolation.
    srcDirname = os.path.dirname(srcPath)

    cmd = 'python '+ testPath
    print 'cmd', cmd

    p = subprocess.Popen(cmd, shell=True,
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         )

    print '       NO OUTPUT YET'
    stdout, stderr = p.communicate()
    print '       NO OUTPUT YET'
    try:
        errput = p.stderr.read(100*1024) # read 100KiB
    except Exception, e:
        errput = ''
    try:
        output = p.stdout.read(100*1024) # read 100KiB
    except Exception, e:
        output = ''
    #print 'output:\n', output
    #print 'errput:\n', errput
    errors = []
    lines = iter(stderr.splitlines())

    print 'lines:\n', '\n'.join(stderr.splitlines())

    for line in lines:
        print line
        m = unittestErrorPattern.search(line)
        if m:
            testFileName = m.group(1)
            lineNum = m.group(2)
            detail = lines.next().strip()
            detail += '\n' + lines.next().strip()
            errors.append((testFileName, lineNum, detail))
            break

    return errors


def findTestsFor(fpath):
    '''Find tests for python files. Returns a unittest test if the
    file has a comment line that looks like "# autotest: unittest"

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

    tests = findTestfileTestsFor(fpath, lines)
    return tests


def findTestfileTestsFor(fpath, lines):
    '''Returns a unittest test file if the inspected file has a comment line 
    that looks like "# autotest: unittest.testfile:tests/test_modname.py"

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
        match = testfileShortPattern.search(line)
        if match:
            fname = os.path.split(fpath)[-1]
            relativeTestPath = 'tests/test_' + fname
            srcDirname = os.path.dirname(fpath)

            testPath = os.path.join(srcDirname, relativeTestPath)
            print 'found testfile pattern', line
            #            function     args              kwargs
            tests.append((testfileFn, (fpath,testPath), dict()))
            break


    return tests


def main():
    thismodule_py = __file__.replace('pyc', 'py')
    print thismodule_py
    for t in findTestsFor(thismodule_py):
        print t

if __name__ == '__main__':
    main()
