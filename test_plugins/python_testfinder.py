#! /usr/bin/python

# autotest: doctest

import os
import re
import sys

from functools import partial

__plugin_version = (1,0)

def log_error(*args):
    msg = ' '.join([str(x) for x in args]) + '\n'
    sys.stderr.write(msg)

pylintErrorPattern = re.compile(r':(\d+):(.*)')

def pylintTestFn(fpath, **kwargs):
    '''run pylint on the module
    '''
    cmd = 'pylint --errors-only --msg-template="{path}:{line}: [{obj}] {msg}" %s' % fpath
    return cmd

def make_report(fpath, output, errput):
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

def find_tests_for(fpath):
    '''Find tests for python files. Should return at least a pylint test.

    >>> find_tests_for('/dev/null')
    []
    '''
    tests = []

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
    lines = contents.splitlines()
    if not lines:
        log_error('empty file', fpath)
        return []

    firstline = lines[0]
    fp.close()

    if not (fpath.endswith('.py')
        or (firstline.startswith('#!') and 'python' in firstline)):
        return []

    report_fn = partial(make_report, fpath)
    tests.append((pylintTestFn, (fpath,), dict(), report_fn))
    return [{
        'make_cmd_fn': pylintTestFn,
        'args': (fpath,),
        'kwargs': {},
        'report_fn': report_fn,
    }]



def main():
    os_py = os.__file__.replace('pyc', 'py')
    print os_py
    for t in find_tests_for(os_py):
        print t

    thismodule_py = __file__.replace('pyc', 'py')
    print thismodule_py
    for t in find_tests_for(thismodule_py):
        print t

if __name__ == '__main__':
    main()
