import MockAPI
import time
import threading


class AnalyticsBuffer:

    # constructor
    def __init__(self,
                 mock_api_instance: MockAPI,
                 buffer_maximum: int = 1,
                 max_time_between_flushes: float = 5,
                 timer_check_interval: float = 0.5):

        self.mock_api_instance = mock_api_instance  # the API the buffer will send to
        self.max_time_between_flushes = max_time_between_flushes  # default 5 seconds
        self.last_flush_time = time.time()  # timestamp of the last flush
        self.timer = None  # measures time between flushes
        self.timer_check_interval = timer_check_interval  # interval in which the timer updates, default 0.5
        # Regarding timer_check_interval: 0.5s was chosen somewhat arbitrarily.
        # A smaller value would make the timer more accurate, but increase background processing cost.
        self.buffer_maximum = buffer_maximum  # max size of buffer, default 5 items
        self.buffer = []  # the buffer
        self.is_flushing = False  # used to prevent multiple flushes at once
        self.consecutive_failures = 0  # counts number of times in a row API fails to respond

        self.start_timer()  # begin the timer

    # track event
    def track(self, event):
        # add the event to the buffer, as long as it is not null, and it is the expected type
        # for the sake of this exercise, events are tuples
        if event is None:
            return
        # My solution for the event in which the API is down for an extended period:
        # No new events are accepted into the buffer.
        # There are pros and cons to this, but it does prevent the buffer from growing unreasonably large.
        elif self.consecutive_failures > 50:
            raise Exception("API unresponsive, no longer accepting events to buffer")

        # the event is added to the buffer
        self.buffer.append(event)

        # check if the buffer is at capacity; if so, attempt to flush
        if len(self.buffer) >= self.buffer_maximum and not self.is_flushing:
            self.flush()

    def start_timer(self):
        # every timer_interval seconds, execute flush_timeout
        self.timer = threading.Timer(self.timer_check_interval, self.flush_timeout_check)
        self.timer.daemon = True  # program will exit if only daemon threads remain (i.e., it cancels itself)
        self.timer.start()

    # if there is something in the buffer, and it has not been flushed after X seconds, flush it
    def flush_timeout_check(self):
        try:
            now = time.time()
            time_since_last_flush = now - self.last_flush_time

            if self.buffer and not self.is_flushing and time_since_last_flush >= self.max_time_between_flushes:
                self.flush()
        finally:
            # restart the timer
            self.start_timer()

    # flush buffer
    def flush(self):
        # only 1 flush can happen at once, to prevent conflicting API responses
        if self.is_flushing:
            raise Exception("Attempted to flush() while another flush() was in progress")
        # don't flush an empty buffer!
        elif not self.buffer:
            raise Exception("Attempted to flush() while buffer was empty")

        # creates a copy of buffer to send(); this prevents errors should buffer change while waiting for a response
        buffer_snapshot = list(self.buffer)
        # we are about to flush!
        self.is_flushing = True
        # sends the snapshot of the buffer and is given a future
        future = self.mock_api_instance.send(buffer_snapshot)

        # inner function for flush() to be ran when future completes
        def on_complete(future_inner):
            try:
                # if future completed successfully, this will proceed
                future_inner.result()
                # empties the buffer of the items sent; items added after sending will not be removed
                self.buffer = self.buffer[len(buffer_snapshot):]
                self.consecutive_failures = 0
            except Exception:
                # future failed to complete
                self.consecutive_failures += 1
            finally:
                self.is_flushing = False

        # on_complete will be called once the future is completed
        future.add_done_callback(on_complete)

# end of AnalyticsBuffer
