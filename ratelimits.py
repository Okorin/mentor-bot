import time


class RateLimit:

    def __init__(self, rate, per):
        self.rate = int(rate)
        self.per = float(per)
        self._uses = self.per
        self._window = 0.0
        self._last = 0.0

    def is_rate_limited(self):
        # get current time
        now = time.time()
        # update last use
        self._last = now

        # we need a new time window if we have the full amount of uses left
        if self._uses == self.rate:
            self._window = now

        # is it time to reset the timer?
        if now > self._window + self.per:
            self._uses = self.rate
            self._window = now

        # if we hit the ratelimit return the amount of seconds until we aren't
        if self._uses == 0:
            return self.per - (now - self._window)

        # decrement the amount of uses we have left
        self._uses -= 1

        # if we hit 0 with this, open a new timing window for checking
        if self._uses == 0:
            self._window = now

        return False
