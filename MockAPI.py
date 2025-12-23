import time
from concurrent.futures import ThreadPoolExecutor, Future


class MockAPI:

    def __init__(self, always_fail: bool = False, delay_seconds: float = 0.01):
        self.always_fail = always_fail  # For testing: when true, the API will never respond
        self.delay_seconds = delay_seconds  # The arbitrary simulated delay

        # records batches and number of calls for testing
        self.sent_buffers = []
        self.call_count = 0

        # I'm only  using single worker thread for simulation/testing to keep things simple
        self.thread_executor = ThreadPoolExecutor(max_workers=1)

    def send(self, received_buffer: list) -> Future:
        self.call_count += 1

        # inner function for send() that simulates asynchronous network latency & delay
        def send_thread_handler(received_buffer_inner: list):
            # simulate network latency with arbitrary delay
            time.sleep(self.delay_seconds)

            # fail, if set to
            if self.always_fail:
                raise Exception("Mock API failure: forced by always_fail")

            # record what was successfully sent
            self.sent_buffers.append(received_buffer_inner)

        # submit the work to a background thread
        return self.thread_executor.submit(send_thread_handler, received_buffer)
