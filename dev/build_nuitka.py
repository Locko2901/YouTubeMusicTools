import subprocess
import threading
import queue

def stream_output(pipe, stream_name, queue):
    print(f"Starting to stream from {stream_name}.")
    try:
        with pipe:
            for line in iter(pipe.readline, ''):
                print(f"{stream_name} output: {line.strip()}")
                queue.put(f"{stream_name}: {line}")
    except Exception as e:
        print(f"Error in {stream_name} stream: {e}")
    print(f"Finished streaming from {stream_name}.")

def print_output(output_queue):
    print("Starting to print output.")
    while True:
        try:
            line = output_queue.get(timeout=1)
            if line == "STOP":
                print("Received STOP signal. Ending print output.")
                break
            print(line, end='')
        except queue.Empty:
            continue

def main():
    command = [
        "python", "-m", "nuitka",
        "--mingw64",
        "--standalone",
        "--windows-console-mode=disable",
        "--include-data-files=media/img.ico=media/img.ico",
        "--enable-plugin=tk-inter",
        "--nofollow-import-to=yt_dlp.extractor.lazy_extractors",
        "--windows-icon-from-ico=media/img.ico",
        "--output-dir=ytmtools.dist",
        "--output-filename=ytmtools",
        "src/main.py"
    ]
    print(f"Command to execute: {' '.join(command)}")
    output_queue = queue.Queue()
    try:
        with subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
        ) as process:
            print("Process started successfully.")
           
            stdout_thread = threading.Thread(target=stream_output, args=(process.stdout, "STDOUT", output_queue))
            stderr_thread = threading.Thread(target=stream_output, args=(process.stderr, "STDERR", output_queue))
            print_thread = threading.Thread(target=print_output, args=(output_queue,))
           
            stdout_thread.start()
            stderr_thread.start()
            print_thread.start()
           
            try:
                while True:
                    if process.poll() is not None:
                        print("Process finished executing.")
                        break
                    if not output_queue.empty():
                        output = output_queue.get_nowait().strip()

                        if "y/n" in output.lower():
                            print("Detected 'y/n' prompt. Responding with 'y'.")
                            process.stdin.write("y\n")
                            process.stdin.flush()
                        
                        elif "yes/no" in output:
                            print("Detected 'y/n' prompt. Responding with 'y'.")
                            process.stdin.write("y\n")
                            process.stdin.flush()

                        elif "Yes/no" in output:
                            print("Detected 'y/n' prompt. Responding with 'y'.")
                            process.stdin.write("y\n")
                            process.stdin.flush()
                        
                        elif "Yes/No" in output:
                            print("Detected 'y/n' prompt. Responding with 'y'.")
                            process.stdin.write("y\n")
                            process.stdin.flush()
                            
                        elif "Is it OK to download" in output:
                            print("Detected download prompt. Responding with 'y'.")
                            process.stdin.write("y\n")
                            process.stdin.flush()
                           
            except Exception as e:
                print(f"An error occurred during process execution: {e}")
            finally:
                print("Cleaning up threads and queues.")
                output_queue.put("STOP")
                stdout_thread.join()
                stderr_thread.join()
                print_thread.join()
    except Exception as e:
        print(f"Failed to start the process: {e}")

if __name__ == "__main__":
    print("Program started.")
    main()
    print("Program finished.")