#!/usr/bin/python

import sys, os, atexit
from signal import SIGTERM

class Daemon(object):

    location = "/tmp"
    umask = 0
    envdir = "/"
    pid = None

    def __init__(self, do="start"):
        """
            do: A command issued to the daemon. Possible values are start, stop, restart
        """

        if self.location == "":
            print "Please override the location before attempting to run this daemon"
            sys.exit(2)

        self.pid = self._check_if_process_exists()
        self._do(do)

    def _start(self):

        if self.pid:
            print "Unable to start daemon, an instance of it is already running with PID: %s " % self.pid
            sys.exit(2)

        try:
            self.pid = os.fork()
            if self.pid > 0:
                sys.exit(0) # exit first parent
        except OSError, e:
            print >> sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)
            sys.exit(1)

        # decouple from parent environment
        os.chdir(self.envdir)
        os.setsid()
        os.umask(self.umask)

        # do second fork
        try:
            self.pid = os.fork()
            if self.pid > 0:
                # exit from second parent, print eventual PID before
                print "Daemon PID %d" % self.pid
                file = open(self.location, "w+")
                file.write(str(self.pid))
                sys.exit(0)
        except OSError, e:
            print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)
            sys.exit(1)

        # handle all the error streams. Ensure they do not interface with the user
        sys.stdin = open('/dev/null', 'r')
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = open('/dev/null', 'w')

        atexit.register(os.getpid())
        self.run()

    def _stop(self):

        if self.pid:
            try:
                os.kill(int(self.pid), SIGTERM)
                print "Daemon with ID %s has been killed" % self.pid
            except OSError:
                print "Process with the id: %s doesn't exist" % self.pid
            except ValueError:
                print "Invalid"
            except OverflowError:
                print "Something went wrong"
        else:
            print "Deamon is not running..."

        if os.path.exists(self.location):
            # remove the .pid file
            os.remove(self.location)

    def _restart(self):
        self._stop()
        self.pid = self._check_if_process_exists()
        self._start()

    def _check_if_process_exists(self):

        if not os.path.exists(self.location):
            return None
        else:
            return open(self.location, "r").readline()

    def _do(self, argument):

        if argument == "start":
            self._start()
        elif argument == "stop":
            self._stop()
        elif argument == "restart":
            self._restart()
        else:
            print "The command '%s' does not exist" % argument
            sys.exit(2)

    def run(self):
        """
        This method should be overridden
        """