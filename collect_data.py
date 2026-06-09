"""
Collect 2 minutes of process telemetry at 1-second intervals using psutil.
Each snapshot captures per-interval deltas for network and disk I/O.
Output: data/live_data.json
"""

import json
import time
import os
from datetime import datetime, timezone

import psutil

DURATION_SECONDS = 120
INTERVAL_SECONDS = 1
OUTPUT_PATH = "data/live_data.json"

ATTRS = ["pid", "name", "cpu_percent", "memory_info",
         "num_threads", "num_handles" if os.name == "nt" else "open_files",
         "connections", "create_time", "status"]


def _snapshot():
    """Return {pid: proc} dict with pre-called io_counters and net baseline."""
    procs = {}
    net_before = psutil.net_io_counters(pernic=False)
    for p in psutil.process_iter(["pid", "name", "status", "create_time",
                                   "num_threads", "memory_info", "cpu_percent"]):
        try:
            io = p.io_counters()
            conns = len(p.net_connections())
            procs[p.pid] = {
                "proc": p,
                "io_read_before": io.read_count,
                "io_write_before": io.write_count,
                "conns": conns,
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return procs, net_before


def _collect_interval(prev_procs, prev_net, snapshot_id: str, ts: str) -> list[dict]:
    """Wait 1s then compute deltas against prev snapshot."""
    time.sleep(INTERVAL_SECONDS)

    net_after = psutil.net_io_counters(pernic=False)
    net_sent_delta = max(0, net_after.bytes_sent - prev_net.bytes_sent)
    net_recv_delta = max(0, net_after.bytes_recv - prev_net.bytes_recv)

    records = []
    for pid, prev in prev_procs.items():
        p = prev["proc"]
        try:
            io = p.io_counters()
            info = p.as_dict(attrs=["name", "cpu_percent", "memory_info",
                                     "num_threads", "create_time", "status"])
            if info["status"] in (psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD):
                continue

            mem_mb = info["memory_info"].rss / (1024 * 1024)
            age = time.time() - info["create_time"]
            disk_read_delta = max(0, io.read_count - prev["io_read_before"])
            disk_write_delta = max(0, io.write_count - prev["io_write_before"])

            # Apportion system-wide net delta equally across visible processes
            n = len(prev_procs) or 1
            records.append({
                "snapshot_id":         snapshot_id,
                "timestamp":           ts,
                "process_name":        info["name"],
                "pid":                 pid,
                "cpu_percent":         round(info["cpu_percent"], 2),
                "memory_mb":           round(mem_mb, 2),
                "thread_count":        info["num_threads"],
                "net_bytes_sent":      round(net_sent_delta / n, 2),
                "net_bytes_recv":      round(net_recv_delta / n, 2),
                "open_connections":    prev["conns"],
                "disk_read_ops":       disk_read_delta,
                "disk_write_ops":      disk_write_delta,
                "process_age_seconds": int(age),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            pass
    return records


def main():
    os.makedirs("data", exist_ok=True)
    all_records = []

    print(f"Collecting {DURATION_SECONDS} snapshots (1/sec)... ", flush=True)

    # Prime cpu_percent (first call always returns 0.0)
    for p in psutil.process_iter(["cpu_percent"]):
        pass
    time.sleep(0.1)

    for i in range(DURATION_SECONDS):
        snap_id = f"snapshot_{i+1:04d}"
        ts = datetime.now(timezone.utc).isoformat()
        prev_procs, prev_net = _snapshot()
        records = _collect_interval(prev_procs, prev_net, snap_id, ts)
        all_records.extend(records)
        print(f"\r  {i+1}/{DURATION_SECONDS}  ({len(records)} procs this tick)", end="", flush=True)

    print(f"\nDone. Total records: {len(all_records)}")
    with open(OUTPUT_PATH, "w") as f:
        json.dump(all_records, f, indent=2)
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
