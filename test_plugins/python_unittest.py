#! /usr/bin/python
'''
Looks for comment lines like this:
    autotest: unittest.testfile : xxxxxxx
or:
    autotest: unittest
'''

# autotest: doctest
# autotest: unittest.testfile:tests/test_python_unittest.py

import os
import re
import sys
from .autotest_comment_parser import parse


__plugin_version = (1,0)


def log_error(*args):
    msg = ' unittest ' + ' '.join([str(x) for x in args]) + '\n'
    sys.stderr.write(msg)

unittestErrorPattern = re.compile('File .*/([^/]+\.py)", line (\d+)')


def testfileFn(srcPath, testPath, **kwargs):
    '''run the unittest file
    If there are no errors, return None
    If there are errors, return a list of (filepath, lineNumber, errorSummary)
    '''
    srcDirname = os.path.dirname(srcPath)

    cmd = 'python '+ testPath
    return cmd


def make_report(output, errput):
    errors = []
    lines = iter(errput.splitlines())

    print 'lines:\n', '\n'.join(errput.splitlines())

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


def find_tests_for(fpath):
    '''Find tests for python files. Returns a unittest test if the
    file has a comment line that looks like "# autotest: unittest"

    >>> find_tests_for('/dev/null')
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

    >>> findTestfileTestsFor('/dev/null', [])
    []
    '''
    test_specs = []

    for line in lines:
        found_autotest = parse(line)
        if not found_autotest:
            continue
        args, kwargs = found_autotest

        if 'unittest' in args:
            # the unit test is assumed to be in the "standard" place
            fname = os.path.split(fpath)[-1]
            relativeTestPath = 'tests/test_' + fname
        else:
            relativeTestPath = kwargs.get('unittest.testfile')

        if relativeTestPath:
            srcDirname = os.path.dirname(fpath)
            testPath = os.path.join(srcDirname, relativeTestPath)

            #print 'found testfile pattern', line
            test_specs.append({
                'make_cmd_fn': testfileFn,
                'args': (fpath, testPath),
                'kwargs': {},
                'report_fn': make_report,
                'env': kwargs.get('env'),
            })
            break

    return test_specs


def main():
    thismodule_py = __file__.replace('pyc', 'py')
    print thismodule_py
    for t in find_tests_for(thismodule_py):
        print t

if __name__ == '__main__':
    main()
