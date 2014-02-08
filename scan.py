#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Copyright (C) 2014 Glencoe Software, Inc. All Rights Reserved.
# Use is subject to license terms supplied in LICENSE.txt
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""
Module documentation
"""

import os
import sys
import stat
import time
import subprocess


def sha1(filename):
    p = subprocess.Popen(["shasum", filename],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    o, e = p.communicate()
    return o[0:37]


class State(object):

    def __init__(self, period=1000):
        self.period = period
        self.total = 0
        self.files = 0
        self.directories = 0
        self.now = time.time()
        self.start = self.now
        self.last = self.now
        self.elapsed = 0
        self.increment = 0
        # During descent
        self.dirpath = None
        self.target = None
        self.stats = None
        self.links = -1

    def enter(self, dirpath):
        self.dirpath = dirpath
        self.directories += 1

    def check(self, filename):
            self.target = os.path.join(self.dirpath, filename)
            self.stats = os.lstat(self.target)
            self.links = self.stats.st_nlink
            self.size = self.stats.st_size
            self.total += self.size
            self.files += 1

            if stat.S_ISLNK(self.stats.st_mode):
                self.checksum = "symlink" + " "*30
            else:
                self.checksum = sha1(self.target)

            self.output()

            if self.files % self.period == 0:
                self.now = time.time()
                self.increment = self.now - self.last
                self.last = self.now
                self.elapsed = self.now - self.start
                print >>sys.stderr, self

    def output(self):
            print "%s\t%s\t%-12s\t%s" % \
                (self.links, self.checksum, self.size, self.target)

    def close(self):
        print >> sys.stderr, self

    def __str__(self):
        return "%s directories with %s files (%s bytes) parsed after %.2f seconds (+%.2f)" % \
            (self.directories, self.files, self.total, self.elapsed, self.increment)

def main(directories):
    print "links\tsha1%s\tsize%s\tname" % (" "*33, " "*8)
    state = State()
    try:
        for directory in directories:
            for dirpath, dirnames, filenames in os.walk(directory):
                filenames.sort()
                dirnames.sort()
                state.enter(dirpath)
                for filename in filenames:
                    state.check(filename)
    except KeyboardInterrupt:
        print >>sys.stderr, "Cancelled"
    finally:
        state.close()


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print "%s dir [dir [dir]]" % sys.argv[0]
        sys.exit(2)
    main(sys.argv[1:])
