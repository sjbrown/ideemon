#! /usr/bin/python
# vim: set fileencoding=utf-8 :

DRUMSTICK = '(   )=3'

def stuff(turkey):
    return turkey[:3] + '₺' + turkey[3:]

def main():
    turkey = stuff(DRUMSTICK)
    print turkey

if __name__ == '__main__':
    main()
