#!/usr/bin/env python
import time
import logging
import threading
logger = logging.getLogger(__name__)


class HomieTimer(threading.Thread):

    def __init__(self, t, f, group=None, target=None, name=None):
        threading.Thread.__init__(self, group=group, target=target, name=name)
        self.daemon = True
        self.t = t
        self.f = f

    def run(self):
        starttime = time.time()
        while True:
            self.f()
            # figure out how much sleep remains, after f() was executed
            delay = self.t - ((time.time() - starttime) % self.t)
            # logger.debug("Delay: {}".format(delay))
            time.sleep(delay)


def main():
    pass

if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Quitting.")
