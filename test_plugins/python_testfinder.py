#! /usr/bin/python

# autotest: doctest

import os
import re
import sys
import subprocess

pluginVersion = (1,0)

def log_error(*args):
    msg = ' '.join([str(x) for x in args]) + '\n'
    sys.stderr.write(msg)

pylintErrorPattern = re.compile(r':(\d+):(.*)')

def pylintTestFn(*args, **kwargs):
    '''run pylint on the module
    '''
    fpath = args[0]
    cmd = 'pylint --errors-only --msg-template="{path}:{line}: [{obj}] {msg}" %s' % fpath

    p = subprocess.Popen(cmd, shell=True,
                         stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE,
                         )

    output = p.stdout.read(100*1024) # read 100KiB
    print 'pylint output', output
    print 'pylint stderr', p.stderr.read()
    errors = []
    for line in output.splitlines():
        if 'but some types could not be inferred' in line:
            # these messages are very often spurious
            continue
        m = pylintErrorPattern.search(line)
        if m:
            lineNum = m.group(1)
            summary = m.group(2).strip()
            errors.append( (fpath, lineNum, summary) )
    return errors

def findTestsFor(fpath):
    '''Find tests for python files. Should return at least a pylint
    test.

    >>> findTestsFor('/dev/null')
    []
    '''
    tests = []

    try:
        fileSize = os.path.getsize(fpath)
    except OSError, ex:
        log_error('could not get file size', fpath, ex)
        return tests

    if fileSize > 100*1024: #bigger than 100KiB
        log_error('file too big', fpath)
        return tests
    try:
        fp = file(fpath)
    except Exception, ex:
        log_error('could not open', fpath, ex)
        return tests
    contents = fp.read()
    lines = contents.splitlines()
    if not lines:
        log_error('empty file', fpath)
        return tests

    firstline = lines[0]
    fp.close()

    if not (fpath.endswith('.py')
        or (firstline.startswith('#!') and 'python' in firstline)):
        return tests

    tests.append((pylintTestFn, (fpath,), dict()))

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
