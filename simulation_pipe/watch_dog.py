import time
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from feature import preprocess_log_lines

class LogHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self._offsets = {}
        self._buffers = {}

    def _is_log_file(self, event):
        return not event.is_directory and event.src_path.endswith(".log")

    def _read_new_lines(self, filepath):
        try:
            current_size = os.path.getsize(filepath)
            offset = self._offsets.get(filepath, 0)

            if current_size < offset:
                offset = 0
                self._buffers[filepath] = ""

            with open(filepath, "r", encoding="utf-8") as file_handle:
                file_handle.seek(offset)
                chunk = file_handle.read()
                self._offsets[filepath] = file_handle.tell()
        except Exception as exc:
            print(f"Error reading {filepath}: {exc}")
            return []

        buffer = self._buffers.get(filepath, "") + chunk
        if not buffer:
            return []

        lines = buffer.splitlines()
        if buffer.endswith(("\n", "\r")):
            self._buffers[filepath] = ""
        else:
            self._buffers[filepath] = lines.pop() if lines else buffer
        return lines

    def _process_file(self, filepath):
        new_lines = self._read_new_lines(filepath)
        if new_lines:
            results = preprocess_log_lines(new_lines, filepath)
            for anomaly, stripped_line in results:
                stripped_line = str(stripped_line)
                if anomaly == 1:  # anomaly detected
                    llm_output = response(stripped_line)
                    alert_developer(stripped_line, llm_output["content"], "developer@example.com")

    def on_created(self, event):
        if self._is_log_file(event):
            print(f"New log file detected: {event.src_path}")
            self._offsets[event.src_path] = 0
            self._buffers[event.src_path] = ""
            self._process_file(event.src_path)

    def on_modified(self, event):
        if self._is_log_file(event):
            self._process_file(event.src_path)

if __name__ == "__main__":
    path = os.path.expanduser("~/etl_pipeline/airflow_home/logs") 
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
