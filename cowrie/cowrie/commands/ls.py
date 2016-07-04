# Copyright (c) 2009 Upi Tamminen <desaster@gmail.com>
# See the COPYRIGHT file for more information

import stat
import time

from cowrie.core.honeypot import HoneyPotCommand
from cowrie.core.fs import *

from cowrie.core.pwd import Passwd, Group

commands = {}

class command_ls(HoneyPotCommand):
    """
    """

    def uid2name(self, uid):
        """
        """
        try:
            return Passwd(self.protocol.cfg).getpwuid(uid)["pw_name"]
        except:
            return str(uid)


    def gid2name(self, gid):
        """
        """
        try:
            return Group(self.protocol.cfg).getgrgid(gid)["gr_name"]
        except:
            return str(gid)


    def call(self):
        """
        """
        path = self.protocol.cwd
        paths = []
        if len(self.args):
            for arg in self.args:
                if not arg.startswith('-'):
                    paths.append(self.protocol.fs.resolve_path(arg,
                        self.protocol.cwd))

        self.show_hidden = False
        func = self.do_ls_normal
        for x in self.args:
            if x.startswith('-') and x.count('l'):
                func = self.do_ls_l
            if x.startswith('-') and x.count('a'):
                self.show_hidden = True

        if not paths:
            func(path)
        else:
            for path in paths:
                func(path)


    def do_ls_normal(self, path):
        """
        """
        try:
            files = self.protocol.fs.get_path(path)
            files.sort()
        except:
            self.write(
                'ls: cannot access %s: No such file or directory\n' % (path,))
            return
        l = [x[A_NAME] for x in files \
            if self.show_hidden or not x[A_NAME].startswith('.')]
        if self.show_hidden:
            l.insert(0, '..')
            l.insert(0, '.')
        if not l:
            return
        count = 0
        maxlen = max([len(x) for x in l])

        try:
            wincols = self.protocol.user.windowSize[1]
        except AttributeError:
            wincols = 80

        perline = int(wincols / (maxlen + 1))
        for f in l:
            if count == perline:
                count = 0
                self.write('\n')
            self.write(f.ljust(maxlen + 1))
            count += 1
        self.write('\n')


    def do_ls_l(self, path):
        """
        """
        try:
            files = self.protocol.fs.get_path(path)[:]
        except:
            self.write(
                'ls: cannot access %s: No such file or directory\n' % (path,))
            return

        if self.show_hidden:
            # FIXME: should grab dotdot off the parent instead
            dot = self.protocol.fs.getfile(path)[:]
            dot[A_NAME] = '.'
            files.append(dot)
            dotdot = self.protocol.fs.getfile(path)[:]
            dotdot[A_NAME] = '..'
            files.append(dotdot)

        files.sort()

        largest = 0
        if len(files):
            largest = max([x[A_SIZE] for x in files])

        for file in files:
            perms = ['-'] * 10

            if file[A_MODE] & stat.S_IRUSR: perms[1] = 'r'
            if file[A_MODE] & stat.S_IWUSR: perms[2] = 'w'
            if file[A_MODE] & stat.S_IXUSR: perms[3] = 'x'
            if file[A_MODE] & stat.S_ISUID: perms[3] = 'S'
            if file[A_MODE] & stat.S_IXUSR and file[A_MODE] & stat.S_ISUID: perms[3] = 's'

            if file[A_MODE] & stat.S_IRGRP: perms[4] = 'r'
            if file[A_MODE] & stat.S_IWGRP: perms[5] = 'w'
            if file[A_MODE] & stat.S_IXGRP: perms[6] = 'x'
            if file[A_MODE] & stat.S_ISGID: perms[6] = 'S'
            if file[A_MODE] & stat.S_IXGRP and file[A_MODE] & stat.S_ISGID: perms[6] = 's'

            if file[A_MODE] & stat.S_IROTH: perms[7] = 'r'
            if file[A_MODE] & stat.S_IWOTH: perms[8] = 'w'
            if file[A_MODE] & stat.S_IXOTH: perms[9] = 'x'
            if file[A_MODE] & stat.S_ISVTX: perms[9] = 'T'
            if file[A_MODE] & stat.S_IXOTH and file[A_MODE] & stat.S_ISVTX: perms[9] = 't'

            linktarget = ''

            if file[A_TYPE] == T_DIR:
                perms[0] = 'd'
            elif file[A_TYPE] == T_LINK:
                perms[0] = 'l'
                linktarget = ' -> %s' % (file[A_TARGET],)

            perms = ''.join(perms)
            ctime = time.localtime(file[A_CTIME])

            l = '%s 1 %s %s %s %s %s%s' % \
                (perms,
                self.uid2name(file[A_UID]),
                self.gid2name(file[A_GID]),
                str(file[A_SIZE]).rjust(len(str(largest))),
                time.strftime('%Y-%m-%d %H:%M', ctime),
                file[A_NAME],
                linktarget)

            self.write(l+'\n')
commands['/bin/ls'] = command_ls
commands['/bin/dir'] = command_ls

