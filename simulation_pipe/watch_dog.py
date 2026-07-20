import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from feature import preprocess_log 

class LogHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".log"):
            print(f"New log file detected: {event.src_path}")
            preprocess_log(event.src_path) 

if __name__ == "__main__":
    path = os.path.expanduser("~/airflow_home/logs") 
    event_handler = LogHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()

    print(f"Watching Airflow logs at: {path}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
