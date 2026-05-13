import queue
import threading

paused = threading.Event()
search_queue: queue.Queue = queue.Queue()
status_lock = threading.Lock()
last_cycle_time: str = "never"
total_new_this_session: int = 0
