import time


class FrameStatsState:
    def __init__(self):
        self.last_frame_start = 0
        self.avg_fps = 0
        self.stats_frame_count = 0
        self.stats_start_time = None
        self.frame_start = None
        self.delta_time = None

    def start_tracking(self):
        self.stats_start_time = time.perf_counter()
        self.last_frame_start = time.perf_counter()

    def track(self):
        self.frame_start = time.perf_counter()
        self.delta_time = self.frame_start - self.last_frame_start
        self.last_frame_start = self.frame_start

        stats_elapsed_time = time.perf_counter() - self.stats_start_time

        # Log stats every 0.5 seconds
        if stats_elapsed_time >= 0.5:
            # Calculate average FPS over the 0.5 second window
            self.avg_fps = self.stats_frame_count / stats_elapsed_time

            # Reset stats counters
            self.stats_start_time = time.perf_counter()
            self.stats_frame_count = 0

    def increment_frame_count(self):
        self.stats_frame_count += 1

    def cap_fps(self, target_fps):
        target_duration = 1 / target_fps
        # Target time when the target_fps is reached
        target_time = self.frame_start + target_duration

        # Sleep/wait until the target_time is reached
        while True:
            remaining_time = target_time - time.perf_counter()

            if remaining_time <= 0:
                break
            
            # Sleep for the majority of the time to save CPU resources
            if remaining_time > 0.001:
                # Sleep for half of the remaining time
                # This methods allow sleeping precision as remaining time approaches zero
                sleep_time = remaining_time * 0.5
                time.sleep(sleep_time)
            
            # Wait until the target time is reached
            else:
                pass

