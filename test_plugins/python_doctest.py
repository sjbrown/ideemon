#! /usr/bin/python

# autotest: doctest

import os
import re
import sys
import doctest

from ideemon.autotest_comment_parser import parse

from functools import partial

__plugin_version = (1,0)

def log_error(*args):
    msg = ' doctest ' + ' '.join([str(x) for x in args]) + '\n'
    sys.stderr.write(msg)

# pattern to match lines like: # autotest: doctest
prefix = r'^\s*#\s*autotest\s*:\s*'
# pattern to match lines like: # autotest: doctest.testfile:test/foo.doctest
testfilePattern = re.compile(prefix + r'doctest\.testfile\s*:(.*)',
                                  re.IGNORECASE)

env_spec_pattern = re.compile(r'env:(.+)\b', re.IGNORECASE)

tb_begin_pattern = 'Traceback (most recent call last):'

doctestErrorPattern = re.compile(r'File .*line (\d+),')
file_error_pattern = re.compile('File .*/([^/]+\.py)", line (\d+)')


def make_doctest_cmd(fpath, **kwargs):
    '''run doctest.testmod on the module
    If there are no errors, return None
    If there are errors, return a list of (filepath, lineNumber, errorSummary)
    '''
    cmd = 'python -m doctest %s' % fpath
    return cmd


def make_testfile_cmd(srcPath, testPath, **kwargs):
    '''run doctest.testfile on the testfile
    If there are no errors, return None
    If there are errors, return a list of (filepath, lineNumber, errorSummary)
    '''

    srcDirname = os.path.dirname(srcPath)
    script = ('import doctest'
              ';import sys'
              ';sys.path.append("%s")'
              ';doctest.testfile("%s", module_relative=False)'
             ) % (srcDirname, testPath)

    cmd = 'python', '-c', script
    print 'cmd', cmd
    return cmd



def scrape_traceback(lines):
    '''
    "lines" should be something like this:

     Traceback (most recent call last):
       File "/python/dist-packages/tornado/testing.py", line 120, in __call__
         result = self.orig_method(*args, **kwargs)
       File "/python/dist-packages/mock.py", line 1190, in patched
         return func(*args, **keywargs)
       File "/home/user/project/tests/foo.py", line 74, in test_foo
         ret = handler.foo(bazbar).result()
       File "/python/dist-packages/tornado/concurrent.py", line 209, in result
         raise_exc_info(self._exc_info)
       File "/python/dist-packages/tornado/gen.py", line 212, in wrapper
         yielded = next(result)
       File "/home/user/project/foo.py", line 160, in foo
         l = [a for (a,b) in some_pairs]
     ValueError: too many values to unpack
     
     ----------------------------------------------------------------------
     Ran 1 test in 0.143s


    If there are no errors, return []
    If there are errors, return the last (filepath, lineNumber, errorSummary)
    '''
    errors = []
    tb_begun = False
    for i, line in enumerate(lines):
        if not tb_begun and line.strip() != tb_begin_pattern:
            continue
        tb_begun = True

        m = file_error_pattern.search(line)
        if m:
            testFileName = m.group(1)
            lineNum = m.group(2)
            detail = lines[i+1].strip()
            detail += '\n' + lines[i+2].strip()
            errors.append((testFileName, lineNum, detail))

    # We want the LAST line that matches
    return errors[-1:]

def make_report(fpath, msg, output, errput):
    lines = output.splitlines()

    tb_errors = scrape_traceback(lines)
    if tb_errors:
        return tb_errors

    lines = iter(lines)
    errors = []
    for line in lines:
        m = doctestErrorPattern.search(line)
        if m:
            lineNum = m.group(1)
            try:
                [lines.next() for x in range(5)] # skip 5 lines forward
                msg += '  Got "%s"' % lines.next().strip()
            except:
                pass
            errors.append((fpath, lineNum, msg))
            break

    return errors


def find_tests_for(fpath):
    '''Find tests for python files. Returns a doctest test if the
    file has a comment line that looks like "# autotest: doctest"

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

    tests = findDoctestsFor(fpath, lines) + findTestfileTestsFor(fpath, lines)
    return tests


def findDoctestsFor(fpath, lines):
    '''Returns a doctest test if the file has a comment line that
    looks like "# autotest: doctest"

    >>> findDoctestsFor('/dev/null', [])
    []
    '''
    tests = []
    test_specs = []

    for line in lines:
        found_autotest = parse(line)
        if not found_autotest:
            continue
        args, kwargs = found_autotest
        if 'doctest' in args:
            report_fn = partial(make_report, fpath, 'doctest failed.')

            test_spec = {'make_cmd_fn': make_doctest_cmd,
                         'args': (fpath,),
                         'kwargs': {},
                         'report_fn': report_fn,
                        }

            env_spec_match = env_spec_pattern.search(line)
            if env_spec_match:
                test_spec['env'] = env_spec_match.group(1)

            test_specs.append(test_spec)
            tests.append((make_doctest_cmd, (fpath,), dict(), report_fn))
            break

    return test_specs


def findTestfileTestsFor(fpath, lines):
    '''Returns a doctest test if the file has a comment line that
    looks like "# autotest: doctest.testfile:test/foo.doctest"

    >>> findTestfileTestsFor('/dev/null', [])
    []
    '''
    tests = []
    test_specs = []

    for line in lines:
        found_autotest = parse(line)
        if not found_autotest:
            continue
        args, kwargs = found_autotest
        relativeTestPath = kwargs.get('doctest.testfile')
        if relativeTestPath:
            #print 'found testfile pattern', line
            srcDirname = os.path.dirname(fpath)
            testPath = os.path.join(srcDirname, relativeTestPath)

            report_fn = partial(make_report, 'doctest testfile failed.')

            test_spec = {'make_cmd_fn': make_testfile_cmd,
                         'args': (fpath, testPath),
                         'kwargs': {},
                         'report_fn': report_fn,
                        }

            env_spec_match = env_spec_pattern.search(line)
            if env_spec_match:
                test_spec['env'] = env_spec_match.group(1)

            test_specs.append(test_spec)
            tests.append((make_testfile_cmd, (fpath,testPath), dict(), report_fn))
            break

    return tests


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
