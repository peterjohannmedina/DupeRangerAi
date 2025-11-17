"""
AiDupeRanger.py

Deprecated: This file is the legacy base implementation. The canonical, actively maintained
entrypoint is `DupeRangerAi.py`. Keep this module for backwards compatibility; prefer
`DupeRangerAi.py` for builds and documentation.
"""

import hashlib
try:
    import xxhash  # fast non-cryptographic hash (xxh64)
except Exception:  # pragma: no cover - optional dependency
    xxhash = None
import json
import mimetypes
import os
import threading
from collections import defaultdict
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait, as_completed
from dataclasses import dataclass, field
from pathlib import Path
import sys
from queue import Empty, Queue
from tkinter import filedialog, messagebox
import tkinter as tk
from tkinter import ttk


class Tooltip:
    """A very small tooltip helper for Tkinter widgets."""
    def __init__(self, widget, text: str, delay: int = 400):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._id = None
        self._tw = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)

    def _schedule(self, _ev=None):
        self._unschedule()
        self._id = self.widget.after(self.delay, self._show)

    def _unschedule(self):
        if self._id:
            try:
                self.widget.after_cancel(self._id)
            except Exception:
                pass
            self._id = None

    def _show(self):
        if self._tw:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 1
        self._tw = tk.Toplevel(self.widget)
        self._tw.wm_overrideredirect(True)
        self._tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self._tw, text=self.text, justify=tk.LEFT, background="#ffffe0", relief=tk.SOLID, borderwidth=1)
        label.pack(ipadx=4, ipady=2)

    def _hide(self, _ev=None):
        self._unschedule()
        if self._tw:
            try:
                self._tw.destroy()
            except Exception:
                pass
            self._tw = None


@dataclass
class FileRecord:
    path: Path
    size: int
    extension: str
    mime: str | None
    hash_value: str | None = None
    fast_hash: int | None = None
    category: str | None = None


@dataclass
class ScanResults:
    root: Path
    files: list[FileRecord] = field(default_factory=list)
    by_extension: dict[str, dict[str, float]] = field(default_factory=dict)
    duplicates: dict[str, list[FileRecord]] = field(default_factory=dict)
    by_category: dict[str, dict[str, float]] = field(default_factory=dict)


class FileClassifier:
    CATEGORY_LABELS = [
        "Photos",
        "Videos",
        "Audio",
        "Documents",
        "Archives",
        "Code",
        "Spreadsheets",
        "Presentations",
        "Backups",
        "Miscellaneous",
    ]

    def __init__(self, device_preference: str = "auto") -> None:
        """
        device_preference: 'auto'|'gpu'|'cpu'
        - 'auto' will use GPU when available else CPU
        - 'gpu' will require CUDA / GPU (raises RuntimeError if unavailable)
        - 'cpu' forces CPU
        """
        try:
            import torch  # type: ignore
            from transformers import pipeline  # type: ignore
        except ImportError as exc:  # pragma: no cover - runtime guard
            raise RuntimeError(
                "AI categorization requires the 'torch' and 'transformers' packages."
            ) from exc

        self._torch = torch

        pref = (device_preference or "auto").lower()
        if pref == "cpu":
            self._device_index = -1
        elif pref == "gpu":
            if not torch.cuda.is_available():
                raise RuntimeError("GPU device requested but CUDA is not available (torch.cuda.is_available() is False).")
            self._device_index = 0
        else:  # auto
            self._device_index = 0 if torch.cuda.is_available() else -1

        # Load zero-shot pipeline; model choice can be adjusted for performance
        # Use a smaller/faster default model for zero-shot classification to reduce memory footprint.
        # 'facebook/bart-large-mnli' works but is large; use 'sshleifer/distilbart-xsum-12-1' or 'typeform/distilbert-base-uncased' for lighter weight.
        # We'll default to a compact but robust NLI model used for zero-shot tasks.
        model_name = "sshleifer/distilbart-xsum-12-1"
        try:
            self._pipeline = pipeline(
                "zero-shot-classification",
                model=model_name,
                device=self._device_index,
            )
        except Exception as e:  # pragma: no cover - fallback handling
            # If loading on GPU triggers an OOM or other issue, try fallback strategies.
            if self._device_index != -1:
                # Try falling back to CPU automatically
                try:
                    self._device_index = -1
                    self._pipeline = pipeline(
                        "zero-shot-classification",
                        model=model_name,
                        device=self._device_index,
                    )
                except Exception:
                    raise
            else:
                raise
        self._lock = threading.Lock()

    @property
    def device_name(self) -> str:
        if self._device_index == -1:
            return "CPU"
        try:
            return self._torch.cuda.get_device_name(self._device_index)
        except Exception:
            return f"GPU:{self._device_index}"

    def classify(self, record: FileRecord) -> str:
        prompt = (
            "Classify this file for organizing. "
            f"Name: {record.path.name}. "
            f"Extension: {record.extension or '<none>'}. "
            f"MIME: {record.mime or 'Unknown'}."
        )
        with self._lock:
            try:
                result = self._pipeline(
                    prompt,
                    candidate_labels=self.CATEGORY_LABELS,
                    multi_label=False,
                )
            except Exception as exc:  # handle unexpected runtime errors (including OOM)
                # If GPU OOM occurs, attempt to fallback to CPU once
                try:
                    if self._device_index != -1:
                        # try switching to CPU
                        self._device_index = -1
                        # recreate pipeline on CPU
                        from transformers import pipeline as _pipeline_factory  # type: ignore

                        self._pipeline = _pipeline_factory(
                            "zero-shot-classification",
                            model=self._pipeline.model.name if hasattr(self._pipeline, 'model') else None,
                            device=-1,
                        )
                        result = self._pipeline(
                            prompt,
                            candidate_labels=self.CATEGORY_LABELS,
                            multi_label=False,
                        )
                        self._lock.release()
                        return result["labels"][0] if result and "labels" in result else "Miscellaneous"
                except Exception:
                    # fall through to return Miscellaneous
                    pass
                return "Miscellaneous"
        if result and "labels" in result:
            return result["labels"][0]
        return "Miscellaneous"


class FileScanner(threading.Thread):
    def __init__(
        self,
        root_path: Path,
        compute_hashes: bool,
        queue: Queue,
        stop_event: threading.Event,
        max_workers: int,
        fast_chunk: int,
        sha_chunk: int,
        classifier: FileClassifier | None,
    ):
        super().__init__(daemon=True)
        self.root_path = root_path
        self.compute_hashes = compute_hashes
        self.queue = queue
        self.stop_event = stop_event
        self.max_workers = max_workers
        # chunk sizes (bytes)
        self.fast_chunk = fast_chunk
        self.sha_chunk = sha_chunk
        self.classifier = classifier

    def run(self) -> None:
        results = ScanResults(root=self.root_path)
        by_extension: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "size": 0})
        duplicates: dict[str, list[FileRecord]] = defaultdict(list)
        by_category: dict[str, dict[str, float]] = defaultdict(lambda: {"count": 0, "size": 0})

        try:
            # Phase 1: fast fingerprint (xxhash) + classification (optional)
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = set()
                for file_path in self._iter_files():
                    if self.stop_event.is_set():
                        break
                    futures.add(executor.submit(self._process_file, file_path))
                    if len(futures) >= self.max_workers * 4:
                        futures = self._drain_futures(
                            futures,
                            results,
                            by_extension,
                            duplicates,
                            by_category,
                        )
                while futures:
                    futures = self._drain_futures(
                        futures,
                        results,
                        by_extension,
                        duplicates,
                        by_category,
                    )

            # Phase 2: when requested, verify candidate duplicate groups using SHA-256
            if self.compute_hashes:
                # group by (size, fast_hash)
                groups: dict[tuple[int, int], list[FileRecord]] = {}
                for rec in results.files:
                    key = (rec.size, rec.fast_hash)
                    groups.setdefault(key, []).append(rec)

                # candidate groups with more than one member
                candidates = [g for g in groups.values() if len(g) > 1]
                if candidates:
                    with ThreadPoolExecutor(max_workers=self.max_workers) as sha_executor:
                        sha_futures = {}
                        for grp in candidates:
                            for rec in grp:
                                # compute sha256 in parallel
                                f = sha_executor.submit(self._hash_file, rec.path, self.sha_chunk)
                                sha_futures[f] = rec

                        for fut in wait(list(sha_futures.keys())).done:
                            pass
                        # collect results as they complete
                        for fut in sha_futures:
                            try:
                                h = fut.result()
                            except Exception:
                                continue
                            rec = sha_futures[fut]
                            rec.hash_value = h
                            # update duplicates map
                            duplicates[h].append(rec)
                            # send updated record to UI for incremental update
                            try:
                                self.queue.put({"type": "record", "record": rec})
                            except Exception:
                                pass

            results.by_extension = {
                ext: {
                    "count": stats["count"],
                    "size": stats["size"],
                }
                for ext, stats in by_extension.items()
            }
            results.duplicates = {
                hash_value: records
                for hash_value, records in duplicates.items()
                if len(records) > 1
            }
            results.by_category = {
                category: {
                    "count": stats["count"],
                    "size": stats["size"],
                }
                for category, stats in by_category.items()
            }
            self.queue.put({"type": "done", "results": results})
        except Exception as exc:  # pylint: disable=broad-except
            self.queue.put({"type": "error", "message": str(exc)})

    def _iter_files(self):
        for path in self.root_path.rglob("*"):
            if path.is_file():
                yield path

    def _drain_futures(
        self,
        futures,
        results: ScanResults,
        by_extension,
        duplicates,
        by_category,
    ):
        done, pending = wait(futures, return_when=FIRST_COMPLETED)
        for future in done:
            if self.stop_event.is_set():
                continue
            try:
                record = future.result()
            except Exception as exc:  # pylint: disable=broad-except
                self.queue.put({"type": "error", "message": str(exc)})
                continue
            if record is None:
                continue
            results.files.append(record)

            ext_key = record.extension or "<no extension>"
            ext_stats = by_extension[ext_key]
            ext_stats["count"] += 1
            ext_stats["size"] += record.size

            if record.hash_value:
                duplicates[record.hash_value].append(record)

            if record.category:
                cat_stats = by_category[record.category]
                cat_stats["count"] += 1
                cat_stats["size"] += record.size

            # Send the complete record to the UI for incremental updates
            self.queue.put({"type": "record", "record": record})
        return pending

    def _inspect_file(self, file_path: Path) -> FileRecord | None:
        try:
            stat = file_path.stat()
            mime, _ = mimetypes.guess_type(file_path.as_uri())
            record = FileRecord(
                path=file_path,
                size=stat.st_size,
                extension=file_path.suffix.lower(),
                mime=mime,
            )
            # Always compute a fast non-cryptographic fingerprint (xxh64) for grouping
            if xxhash is not None:
                try:
                    record.fast_hash = self._fast_hash_file(file_path, chunk_size=self.fast_chunk)
                except Exception:
                    record.fast_hash = None
            return record
        except (PermissionError, FileNotFoundError):
            return None

    def _process_file(self, file_path: Path) -> FileRecord | None:
        if self.stop_event.is_set():
            return None
        record = self._inspect_file(file_path)
        if record is None:
            return None
        if self.classifier:
            try:
                record.category = self.classifier.classify(record)
            except Exception:  # pylint: disable=broad-except
                record.category = None
        return record

    @staticmethod
    def _hash_file(file_path: Path, chunk_size: int = 1_048_576) -> str:
        sha256 = hashlib.sha256()
        with file_path.open("rb") as stream:
            while chunk := stream.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def _fast_hash_file(file_path: Path, chunk_size: int = 8_388_608) -> int:
        """Compute a fast 64-bit xxhash fingerprint (returns int) or raise if xxhash missing."""
        if xxhash is None:
            raise RuntimeError("xxhash not available")
        h = xxhash.xxh64()
        with file_path.open("rb") as stream:
            while chunk := stream.read(chunk_size):
                h.update(chunk)
        return h.intdigest()


class FileOrganizerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("ZFS File Organizer Helper")
        self.root.geometry("960x640")

        self.queue: Queue = Queue()
        self.stop_event = threading.Event()
        self.scanner: FileScanner | None = None
        self.current_results: ScanResults | None = None
        self.classifier: FileClassifier | None = None
        # Live incremental UI state (maps for fast updates)
        self._ext_items: dict[str, str] = {}
        self._dup_items: dict[str, str] = {}
        self._cat_items: dict[str, str] = {}
        # store interpreter info for debugging installs
        self._interpreter = sys.executable

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.after(200, self._poll_queue)

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        path_frame = ttk.Frame(self.root, padding=10)
        path_frame.grid(column=0, row=0, sticky="nsew")
        path_frame.columnconfigure(1, weight=1)

        ttk.Label(path_frame, text="Target directory:").grid(column=0, row=0, sticky="w")
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        self.path_entry.grid(column=1, row=0, sticky="ew", padx=6)

        ttk.Button(path_frame, text="Browse", command=self._browse_directory).grid(column=2, row=0, padx=6)

        options_frame = ttk.Frame(self.root, padding=(10, 0))
        options_frame.grid(column=0, row=1, sticky="ew")
        options_frame.columnconfigure(0, weight=1)

        self.hash_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            options_frame,
            text="Compute SHA-256 hashes (slow; enables duplicate detection)",
            variable=self.hash_var,
        ).grid(column=0, row=0, sticky="w")

        self.classifier_var = tk.BooleanVar(value=False)
        self.classifier_label_var = tk.StringVar(value="AI categorization: disabled")
        ttk.Checkbutton(
            options_frame,
            text="Enable AI categorization (torch + transformers)",
            variable=self.classifier_var,
            command=self._on_classifier_toggle,
        ).grid(column=0, row=1, sticky="w", pady=(4, 0))
        ttk.Label(options_frame, textvariable=self.classifier_label_var).grid(column=0, row=2, sticky="w")

        # Interpreter info and AI env verification
        interp_frame = ttk.Frame(options_frame)
        interp_frame.grid(column=0, row=5, sticky="w", pady=(6,0))
        self.interpreter_var = tk.StringVar(value=self._interpreter)
        ttk.Label(interp_frame, text="Interpreter:").grid(column=0, row=0, sticky="w")
        ttk.Label(interp_frame, textvariable=self.interpreter_var).grid(column=1, row=0, sticky="w", padx=(6,0))
        ttk.Button(interp_frame, text="Verify AI env", command=self._verify_ai_env).grid(column=2, row=0, sticky="w", padx=(8,0))

        # Device selection for AI (auto/gpu/cpu)
        self.device_choice_var = tk.StringVar(value="auto")
        device_frame = ttk.Frame(options_frame)
        device_frame.grid(column=0, row=4, sticky="w", pady=(6, 0))
        ttk.Label(device_frame, text="Compute device:").grid(column=0, row=0, sticky="w")
        device_menu = ttk.OptionMenu(
            device_frame,
            self.device_choice_var,
            "auto",
            "auto",
            "gpu",
            "cpu",
            command=lambda _v: self._on_device_change(),
        )
        device_menu.grid(column=1, row=0, sticky="w", padx=(6, 0))
        ttk.Label(device_frame, text="(auto = GPU if available)").grid(column=2, row=0, sticky="w", padx=(8, 0))

        buttons_frame = ttk.Frame(options_frame)
        buttons_frame.grid(column=1, row=0, rowspan=3, sticky="e")

        self.scan_button = ttk.Button(buttons_frame, text="Scan", command=self._on_scan_clicked)
        self.scan_button.grid(column=0, row=0, padx=(0, 6))

        self.stop_button = ttk.Button(buttons_frame, text="Stop", command=self._on_stop_clicked, state="disabled")
        self.stop_button.grid(column=1, row=0)

        self.progress_var = tk.StringVar(value="Idle")
        ttk.Label(options_frame, textvariable=self.progress_var).grid(column=0, row=3, columnspan=2, sticky="w", pady=(6, 0))

        # Worker and chunk-size tuning
        # Autodetect default workers
        default_workers = max(4, min(32, (os.cpu_count() or 4) * 2))
        self.worker_count_var = tk.IntVar(value=default_workers)
        worker_frame = ttk.Frame(options_frame)
        worker_frame.grid(column=1, row=3, sticky="e")
        ttk.Label(worker_frame, text="Workers:").grid(column=0, row=0, sticky="e")
        self.worker_spin = ttk.Spinbox(worker_frame, from_=1, to=128, width=5, textvariable=self.worker_count_var)
        self.worker_spin.grid(column=1, row=0, sticky="w", padx=(6,0))

        # Chunk sizes for fast hash and sha256 (in MB)
        # fast: integer MB (e.g. 4..32). sha: fractional MB allowed (e.g. 0.5, 1.0)
        self.fast_chunk_var = tk.IntVar(value=8)   # 8 MB
        self.sha_chunk_var = tk.DoubleVar(value=1.0)    # 1 MB
        chunk_frame = ttk.Frame(options_frame)
        chunk_frame.grid(column=0, row=6, columnspan=2, sticky="w", pady=(6,0))
        ttk.Label(chunk_frame, text="Fast chunk (MB):").grid(column=0, row=0, sticky="w")
        self.fast_chunk_entry = ttk.Entry(chunk_frame, textvariable=self.fast_chunk_var, width=6)
        self.fast_chunk_entry.grid(column=1, row=0, sticky="w", padx=(6,8))
        ttk.Label(chunk_frame, text="SHA chunk (MB):").grid(column=2, row=0, sticky="w")
        self.sha_chunk_entry = ttk.Entry(chunk_frame, textvariable=self.sha_chunk_var, width=6)
        self.sha_chunk_entry.grid(column=3, row=0, sticky="w", padx=(6,0))

        # Tooltips with recommendations
        Tooltip(self.fast_chunk_entry, "Fast chunk (MB): 4–16 MB recommended for local NVMe; 1–4 MB for SMB/NAS.")
        Tooltip(self.sha_chunk_entry, "SHA chunk (MB): 0.5–2 MB recommended; 1 MB is a good default.")

        notebook = ttk.Notebook(self.root)
        notebook.grid(column=0, row=2, sticky="nsew", padx=10, pady=10)

        self.extensions_tree = self._create_tree(
            notebook,
            columns=("count", "size", "mime"),
            headings={
                "#0": "Extension",
                "count": "Count",
                "size": "Size (MB)",
                "mime": "Common MIME",
            },
            widths={"#0": 160, "count": 100, "size": 120, "mime": 320},
        )
        notebook.add(self.extensions_tree, text="By Extension")

        self.duplicates_tree = self._create_tree(
            notebook,
            columns=("count", "sample"),
            headings={"#0": "Hash", "count": "Instances", "sample": "Sample file"},
            widths={"#0": 320, "count": 100, "sample": 420},
        )
        notebook.add(self.duplicates_tree, text="Duplicates")

        self.categories_tree = self._create_tree(
            notebook,
            columns=("count", "size"),
            headings={"#0": "Category", "count": "Count", "size": "Size (MB)"},
            widths={"#0": 200, "count": 100, "size": 140},
        )
        notebook.add(self.categories_tree, text="AI Categories")

        summary_frame = ttk.Frame(self.root, padding=10)
        summary_frame.grid(column=0, row=3, sticky="ew")
        summary_frame.columnconfigure(0, weight=1)

        ttk.Button(summary_frame, text="Export summary", command=self._export_summary).grid(column=0, row=0, sticky="w")
        ttk.Button(summary_frame, text="Show HF cache", command=self._show_hf_cache).grid(column=1, row=0, sticky="w", padx=(8,0))

    def _create_tree(self, parent, columns, headings, widths):
        tree = ttk.Treeview(parent, columns=columns, show="tree headings", selectmode="browse")
        tree.grid(sticky="nsew")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        for column in columns:
            tree.heading(column, text=headings[column])
            tree.column(column, width=widths.get(column, 120), anchor=tk.W)
        tree.heading("#0", text=headings["#0"])
        tree.column("#0", width=widths.get("#0", 200), anchor=tk.W)

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        return tree

    def _browse_directory(self) -> None:
        directory = filedialog.askdirectory()
        if directory:
            self.path_var.set(directory)

    def _on_scan_clicked(self) -> None:
        path_value = self.path_var.get().strip()
        if not path_value:
            messagebox.showwarning("Missing path", "Please select a directory to scan.")
            return

        root_path = Path(path_value)
        if not root_path.exists() or not root_path.is_dir():
            messagebox.showerror("Invalid path", "The selected path does not exist or is not a directory.")
            return

        if self.scanner and self.scanner.is_alive():
            messagebox.showinfo("Scan in progress", "A scan is already running.")
            return

        classifier = None
        if self.classifier_var.get():
            classifier = self._ensure_classifier()
            if classifier is None:
                return

        # initialize live summaries and UI maps
        self._ext_items.clear()
        self._dup_items.clear()
        self._cat_items.clear()

        self._set_ui_state(scanning=True)
        self.progress_var.set(f"Scanning {root_path} ...")
        self.stop_event.clear()
        self._clear_results()

        self.scanner = FileScanner(
            root_path=root_path,
            compute_hashes=self.hash_var.get(),
            queue=self.queue,
            stop_event=self.stop_event,
            max_workers=self._determine_worker_count(),
            fast_chunk=int(self.fast_chunk_var.get() * 1024 * 1024),
            sha_chunk=int(float(self.sha_chunk_var.get()) * 1024 * 1024),
            classifier=classifier,
        )
        self.scanner.start()

    def _on_stop_clicked(self) -> None:
        if self.scanner and self.scanner.is_alive():
            self.stop_event.set()
            self.progress_var.set("Stopping scan ...")

    def _poll_queue(self) -> None:
        try:
            while True:
                message = self.queue.get_nowait()
                message_type = message.get("type")

                if message_type == "progress":
                    self.progress_var.set(f"Scanning: {message.get('path', '')}")
                elif message_type == "record":
                    record = message.get("record")
                    if record is not None:
                        self._handle_record(record)
                        # update progress with the path as well
                        self.progress_var.set(f"Scanning: {getattr(record, 'path', '')}")
                elif message_type == "done":
                    self._handle_results(message["results"])
                    self._set_ui_state(scanning=False)
                elif message_type == "error":
                    messagebox.showerror("Scan error", message.get("message", "Unknown error"))
                    self._set_ui_state(scanning=False)
        except Empty:
            pass
        finally:
            self.root.after(200, self._poll_queue)

    def _handle_results(self, results: ScanResults) -> None:
        self.current_results = results
        self.progress_var.set(f"Scan complete: {len(results.files)} files")
        self._populate_extensions(results)
        self._populate_duplicates(results)
        self._populate_categories(results)

    def _populate_extensions(self, results: ScanResults) -> None:
        for item in self.extensions_tree.get_children():
            self.extensions_tree.delete(item)

        summary = {}
        for record in results.files:
            key = record.extension or "<no extension>"
            mime = record.mime or "Unknown"
            data = summary.setdefault(key, {"count": 0, "size": 0, "mime": mime})
            data["count"] += 1
            data["size"] += record.size
            if data["mime"] == "Unknown" and record.mime:
                data["mime"] = record.mime

        for ext, info in sorted(summary.items(), key=lambda item: item[1]["count"], reverse=True):
            size_mb = info["size"] / (1024 * 1024)
            self.extensions_tree.insert(
                "", tk.END, text=ext, values=(info["count"], f"{size_mb:.2f}", info["mime"]) 
            )

    def _handle_record(self, record: FileRecord) -> None:
        """Incrementally update UI trees with a single FileRecord."""
        # Update internal structures and treeviews for extensions
        ext = record.extension or "<no extension>"
        # update ext summary
        if ext in self._ext_items:
            item_id = self._ext_items[ext]
            cur_values = self.extensions_tree.item(item_id, "values")
            try:
                cur_count = int(cur_values[0])
                cur_size = float(cur_values[1])
            except Exception:
                cur_count = 0
                cur_size = 0.0
            new_count = cur_count + 1
            new_size_mb = (cur_size * 1.0) + (record.size / (1024 * 1024))
            mime = cur_values[2] if len(cur_values) > 2 else (record.mime or "Unknown")
            self.extensions_tree.item(item_id, values=(new_count, f"{new_size_mb:.2f}", mime))
        else:
            size_mb = record.size / (1024 * 1024)
            item_id = self.extensions_tree.insert("", tk.END, text=ext, values=(1, f"{size_mb:.2f}", record.mime or "Unknown"))
            self._ext_items[ext] = item_id

        # Update duplicates (by hash)
        if record.hash_value:
            h = record.hash_value
            if h in self._dup_items:
                item_id = self._dup_items[h]
                cur_values = self.duplicates_tree.item(item_id, "values")
                try:
                    cur_count = int(cur_values[0])
                except Exception:
                    cur_count = 0
                new_count = cur_count + 1
                sample = cur_values[1] if len(cur_values) > 1 else str(record.path)
                self.duplicates_tree.item(item_id, values=(new_count, sample))
            else:
                item_id = self.duplicates_tree.insert("", tk.END, text=record.hash_value, values=(1, str(record.path)))
                self._dup_items[h] = item_id

        # Update categories
        if record.category:
            cat = record.category
            if cat in self._cat_items:
                item_id = self._cat_items[cat]
                cur_values = self.categories_tree.item(item_id, "values")
                try:
                    cur_count = int(cur_values[0])
                    cur_size = float(cur_values[1])
                except Exception:
                    cur_count = 0
                    cur_size = 0.0
                new_count = cur_count + 1
                new_size_mb = cur_size + (record.size / (1024 * 1024))
                self.categories_tree.item(item_id, values=(new_count, f"{new_size_mb:.2f}"))
            else:
                size_mb = record.size / (1024 * 1024)
                item_id = self.categories_tree.insert("", tk.END, text=cat, values=(1, f"{size_mb:.2f}"))
                self._cat_items[cat] = item_id

    def _populate_duplicates(self, results: ScanResults) -> None:
        for item in self.duplicates_tree.get_children():
            self.duplicates_tree.delete(item)

        duplicate_items = sorted(results.duplicates.items(), key=lambda item: len(item[1]), reverse=True)
        for hash_value, records in duplicate_items:
            sample_path = str(records[0].path)
            self.duplicates_tree.insert("", tk.END, text=hash_value, values=(len(records), sample_path))

        if not duplicate_items and self.hash_var.get():
            self.progress_var.set("Scan complete: no duplicate hashes detected")

    def _populate_categories(self, results: ScanResults) -> None:
        for item in self.categories_tree.get_children():
            self.categories_tree.delete(item)

        if not results.by_category:
            return

        for category, stats in sorted(
            results.by_category.items(), key=lambda item: item[1]["count"], reverse=True
        ):
            size_mb = stats["size"] / (1024 * 1024)
            self.categories_tree.insert(
                "", tk.END, text=category, values=(stats["count"], f"{size_mb:.2f}")
            )

    def _show_hf_cache(self) -> None:
        """Display the Hugging Face cache path and list the largest model files (top 10)."""
        try:
            from pathlib import Path
            import os

            home = Path(os.path.expanduser("~"))
            default_cache = home / ".cache" / "huggingface" / "hub"
            cache_dir = os.environ.get("HF_HOME") or os.environ.get("TRANSFORMERS_CACHE") or str(default_cache)
            cache_path = Path(cache_dir)
            if not cache_path.exists():
                messagebox.showinfo("HF cache", f"Cache directory does not exist: {cache_path}")
                return

            # find large files under cache (recursively)
            files = []
            for p in cache_path.rglob("*"):
                if p.is_file():
                    try:
                        files.append((p, p.stat().st_size))
                    except Exception:
                        continue
            files.sort(key=lambda t: t[1], reverse=True)
            top = files[:10]

            text = [f"Hugging Face cache: {cache_path}", "", "Largest files:"]
            if not top:
                text.append("(no files found)")
            else:
                for p, size in top:
                    mb = size / (1024 * 1024)
                    text.append(f"{mb:.2f} MB - {p}")

            messagebox.showinfo("HF cache contents", "\n".join(text))
        except Exception as exc:
            messagebox.showerror("HF cache error", str(exc))

    def _custom_json_encoder(self, obj):  # type: ignore[no-untyped-def]
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, FileRecord):
            return {
                "path": str(obj.path),
                "size": obj.size,
                "extension": obj.extension,
                "mime": obj.mime,
                "hash": obj.hash_value,
                "category": obj.category,
            }
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    def _export_summary(self) -> None:
        if not self.current_results:
            messagebox.showinfo("No data", "Run a scan before exporting.")
            return

        export_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=(("JSON Files", "*.json"), ("All Files", "*.*")),
            initialfile="zfs_scan_summary.json",
        )
        if not export_path:
            return

        try:
            data = {
                "root": str(self.current_results.root),
                "extension_summary": self.current_results.by_extension,
                "category_summary": self.current_results.by_category,
                "duplicates": {
                    hash_value: [str(record.path) for record in records]
                    for hash_value, records in self.current_results.duplicates.items()
                },
            }
            with open(export_path, "w", encoding="utf-8") as stream:
                json.dump(data, stream, indent=2)
            messagebox.showinfo("Export complete", f"Summary saved to {export_path}")
        except OSError as exc:
            messagebox.showerror("Export failed", str(exc))

    def _set_ui_state(self, scanning: bool) -> None:
        if scanning:
            self.scan_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
        else:
            self.scan_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

    def _clear_results(self) -> None:
        for tree in (self.extensions_tree, self.duplicates_tree, self.categories_tree):
            for item in tree.get_children():
                tree.delete(item)
        self.current_results = None

    def _determine_worker_count(self) -> int:
        # If UI provides a value, prefer that (useful for tuning)
        try:
            val = int(getattr(self, 'worker_count_var').get())
            if val > 0:
                return val
        except Exception:
            pass
        cpu_total = os.cpu_count() or 4
        return max(4, min(32, cpu_total * 2))

    def _ensure_classifier(self) -> FileClassifier | None:
        if self.classifier:
            self.classifier_label_var.set(f"AI categorization: {self.classifier.device_name}")
            return self.classifier
        try:
            device_pref = (self.device_choice_var.get() if hasattr(self, "device_choice_var") else "auto").lower()
            classifier = FileClassifier(device_preference=device_pref)
        except RuntimeError as exc:
            # Provide actionable installer hint and show which interpreter is in use
            hint = f"{str(exc)}\n\nInterpreter: {self._interpreter}\nPlease run the installer to add required packages into that environment:\n  .\\install_deps.ps1 -UseGPU\n(or run without -UseGPU for CPU-only)"
            messagebox.showerror("AI categorization unavailable", hint)
            self.classifier_var.set(False)
            self.classifier_label_var.set("AI categorization: disabled")
            return None
        self.classifier = classifier
        self.classifier_label_var.set(f"AI categorization: {classifier.device_name}")
        return classifier

    def _verify_ai_env(self) -> None:
        """Check that torch and transformers import correctly in the running interpreter and report CUDA availability."""
        try:
            import importlib
            torch = importlib.import_module('torch')
            transformers = importlib.import_module('transformers')
            parts = [f"python: {sys.executable} ({sys.version.splitlines()[0]})",
                     f"torch: {getattr(torch, '__version__', 'unknown')}",
                     f"torch.version.cuda (build): {getattr(torch.version, 'cuda', None)}",
                     f"CUDA available: {torch.cuda.is_available()}"]
            if torch.cuda.is_available():
                try:
                    parts.append(f"GPU count: {torch.cuda.device_count()}")
                    parts.append(f"GPU name: {torch.cuda.get_device_name(0)}")
                except Exception:
                    pass
            messagebox.showinfo("AI environment check", "\n".join(parts))
        except Exception as exc:
            messagebox.showerror("AI environment check failed",
                                 f"Failed to import required AI packages in interpreter:\n{sys.executable}\n\nError: {exc}\n\nRun .\\install_deps.ps1 -UseGPU to install the dependencies into the venv.")

    def _on_classifier_toggle(self) -> None:
        if self.classifier_var.get():
            self._ensure_classifier()
        else:
            self.classifier_label_var.set("AI categorization: disabled")

    def _on_device_change(self) -> None:
        """Called when compute device selection changes. If a classifier is loaded, prompt to recreate it on the new device?"""
        if not self.classifier:
            return
        if not messagebox.askyesno(
            "Change compute device",
            "Change compute device and reload the AI model now? This will free and reload model resources."
        ):
            return
        # Tear down existing classifier and recreate with new preference
        self.classifier = None
        classifier = self._ensure_classifier()
        if classifier is None:
            return
        self.classifier = classifier

    def _on_close(self) -> None:
        if self.scanner and self.scanner.is_alive():
            if not messagebox.askyesno(
                "Scan in progress", "A scan is running. Do you want to stop it and exit?"
            ):
                return
            self.stop_event.set()
            self.scanner.join(timeout=2)
        self.root.destroy()


def main() -> None:
    mimetypes.init()
    root = tk.Tk()
    app = FileOrganizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    # Maintain backwards compatibility: redirect calls to canonical entrypoint.
    import warnings
    from importlib import import_module

    warnings.warn(
        "AiDupeRanger is deprecated — please use DupeRangerAi.py as the primary entrypoint.",
        DeprecationWarning,
    )
    try:
        mod = import_module("DupeRangerAi")
        entry = getattr(mod, "main")
        entry()
    except Exception:
        # Fallback to local main if import fails
        main()
