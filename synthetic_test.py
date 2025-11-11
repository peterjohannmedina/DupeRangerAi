import time
import tempfile
import shutil
from pathlib import Path
from queue import Queue
import threading

from AiDupeRanger_grok import FileScanner, ScanResults


def make_test_files(root: Path, num_unique=50, dup_per=3, small=True):
    files = []
    if small:
        base = b"hello world\n" * 10
    else:
        base = b"x" * (1024 * 1024 * 2)  # 2MB
    for i in range(num_unique):
        p = root / f"file_{i}.dat"
        p.write_bytes(base + bytes(str(i), 'utf-8'))
        files.append(p)
        # create duplicates
        for d in range(dup_per):
            q = root / f"file_{i}_dup{d}.dat"
            shutil.copy(p, q)
            files.append(q)
    return files


def run_synthetic_test():
    tmp = Path(tempfile.mkdtemp(prefix="duperanger-test-"))
    try:
        print("Creating test files in", tmp)
        make_test_files(tmp, num_unique=30, dup_per=2, small=True)

        q = Queue()
        stop_event = threading.Event()
        max_workers = 8

        scanner = FileScanner(root_path=tmp, compute_hashes=True, queue=q, stop_event=stop_event, max_workers=max_workers, fast_chunk=8*1024*1024, sha_chunk=1024*1024, classifier=None)
        start = time.time()
        scanner.start()
        results = None
        while True:
            msg = q.get()
            if msg.get("type") == "done":
                results = msg.get("results")
                break
        elapsed = time.time() - start
        print(f"Scan complete in {elapsed:.2f}s, files={len(results.files)}")
        print(f"Duplicate groups: {len(results.duplicates)}")
        for h, recs in results.duplicates.items():
            print(h, [str(r.path.name) for r in recs])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    run_synthetic_test()
