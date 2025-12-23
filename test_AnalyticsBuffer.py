import unittest
import time
from AnalyticsBuffer import AnalyticsBuffer
from MockAPI import MockAPI


class test_analytics_buffer(unittest.TestCase):

    def test_flush_at_buffer_max(self):
        api = MockAPI()
        buffer = AnalyticsBuffer(mock_api_instance=api, buffer_maximum=5, max_time_between_flushes=1000)  # disable timer flush

        buffer.track(("event1",))
        buffer.track(("event2",))
        buffer.track(("event3",))
        buffer.track(("event4",))
        buffer.track(("event5",))

        # Need to give time for the API to respond
        # Note: I was hesitant about including this, as the task said:
        # "Demonstrate how you test time-dependant logic without making the test wait"
        # However, unlike the flush timer, this is a very short delay,
        # and I thought that demonstrating the "asynchronicity" of the code was important.
        time.sleep(0.015)

        # has the API been called the expected no. times?
        self.assertEqual(api.call_count, 1)
        # was only 1 buffer received?
        self.assertEqual(len(api.sent_buffers), 1)
        # does the received buffer match the sent one?
        self.assertEqual(api.sent_buffers[0], [("event1",), ("event2",), ("event3",), ("event4",), ("event5",)])
        # is the buffer now empty?
        self.assertEqual(buffer.buffer, [])

        # we'll use different ones in later tests
        del api
        del buffer

    def test_flush_on_timeout(self):
        api = MockAPI(delay_seconds=0)
        buffer = AnalyticsBuffer(api, max_time_between_flushes=5)

        buffer.track(("event1",))
        buffer.track(("event2",))

        # Simulate time passing
        buffer.last_flush_time -= 10

        # force a timeout check
        buffer.flush_timeout_check()

        # Need to give time for the API to respond
        time.sleep(0.015)

        # has the API been called the expected no. times?
        self.assertEqual(api.call_count, 1)
        # does the received buffer match the sent one?
        self.assertEqual(api.sent_buffers[0], [("event1",), ("event2",)])

        # we'll use different ones in later tests
        del api
        del buffer

    def test_api_failure_keeps_buffer(self):
        api = MockAPI(always_fail=True, delay_seconds=0)
        buffer = AnalyticsBuffer(api, buffer_maximum=2)

        buffer.track(("event1",))
        buffer.track(("event2",))

        time.sleep(0.01)

        # was the API called?
        self.assertEqual(api.call_count, 1)
        # are the items still in the buffer?
        self.assertEqual(buffer.buffer, [("event1",), ("event2",)])
        # did the buffer fail?
        self.assertEqual(buffer.consecutive_failures, 1)

        # we'll use different ones in later tests
        del api
        del buffer

    def test_track_is_non_blocking(self):
        api = MockAPI(delay_seconds=0.5)
        buffer = AnalyticsBuffer(mock_api_instance=api, buffer_maximum=1)

        start = time.time()
        buffer.track(("event1",))
        end = time.time()

        # did track() have to wait 0.5s for the API to respond?
        self.assertLess(end - start, 0.1)

        # we'll use different ones in later tests
        del api
        del buffer


if __name__ == '__main__':
    unittest.main()
