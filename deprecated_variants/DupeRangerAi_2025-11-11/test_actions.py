#!/usr/bin/env python3
"""
Test script for AiDupeRanger_grok's new action features.
Creates a temporary directory with duplicates and tests the action application.
"""
""
Test script for DupeRangerAi's action features (packaged copy).
"""
from pathlib import Path
from queue import Queue
import threading
import time

from DupeRangerAi import FileScanner, ScanResults, FileOrganizerApp
import tkinter as tk


def create_test_files(root: Path):
    """Create test files with known duplicates."""
    # Create unique files
    files = []
    for i in range(3):
        p = root / f"file_{i}.txt"
        p.write_text(f"Content {i}\n" * 10)
        files.append(p)

    # Create duplicates
    dup1 = root / "file_0_copy.txt"
    shutil.copy(files[0], dup1)
    files.append(dup1)

    dup2 = root / "file_1_copy.txt"
    shutil.copy(files[1], dup2)
    files.append(dup2)

    # Create older duplicate by touching mtime
    dup3 = root / "file_0_older.txt"
    shutil.copy(files[0], dup3)
    # Make it older
    import os
    os.utime(dup3, (dup3.stat().st_atime - 3600, dup3.stat().st_mtime - 3600))
    files.append(dup3)

    return files


def test_actions():
    """Test the action application logic."""
    tmp = Path(tempfile.mkdtemp(prefix="action-test-"))
    try:
        print(f"Testing actions in {tmp}")
        create_test_files(tmp)

        # Scan the directory
        q = Queue()
        stop_event = threading.Event()
        scanner = FileScanner(
            root_path=tmp,
            compute_hashes=True,
            queue=q,
            stop_event=stop_event,
            max_workers=4,
            fast_chunk=8*1024*1024,
            sha_chunk=1024*1024,
            classifier=None
        )

        scanner.start()
        results = None
        while True:
            msg = q.get()
            if msg.get("type") == "done":
                results = msg.get("results")
                break

        print(f"Scan complete: {len(results.files)} files, {len(results.duplicates)} duplicate groups")

        # Simulate the app for testing actions
        root = tk.Tk()
        root.withdraw()  # Hide the window
        app = FileOrganizerApp(root)
        app.current_results = results

        # Test duplicate handling (retain oldest, rename others)
        print("\nTesting duplicate handling...")
        app.dup_handle_var.set(True)
        app.retain_choice_var.set("oldest")
        app.dry_run_var.set(False)  # Actually apply changes

        summary = app._build_action_summary()
        print("Planned actions:")
        for line in summary:
            print(f"  {line}")

        print("\nApplying actions...")
        app._apply_actions(dry_run=False)

        # Check results
        print("\nFiles after actions:")
        for f in sorted(tmp.rglob("*")):
            if f.is_file():
                mtime = f.stat().st_mtime
                print(f"  {f.name} (mtime: {time.ctime(mtime)})")

        print("\nTest complete!")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        root.destroy()


if __name__ == '__main__':
    test_actions()