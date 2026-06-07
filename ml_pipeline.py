# team2_data.py — Project Sentinel / Team 2: Data Generation + ML Detection
#
# DESIGN RATIONALE (read before modifying):
#
#   1. Process-specific baseline distributions (PROCESS_PROFILES) tighten
#      intra-class variance. IsolationForest isolates points that require few
#      random splits — a point far from the dense cluster needs fewer splits,
#      so tighter normals make injected anomalies score more negatively.
#
#   2. Correlated multi-feature anomalies (cpu_mem_burst, disk_net_inversion)
#      exploit IsolationForest's multi-dimensional partition space. A univariate
#      z-score would miss "high disk AND near-zero network" as individual values
#      may not cross thresholds; IF catches the joint rarity.
#
#   3. Anomaly injection at exactly CONTAMINATION fraction → the model's
#      decision threshold aligns with ground truth, minimising false
#      positives / negatives at the contamination boundary.
#
#   4. fit() once, then score_samples() + predict() separately → avoids the
#      double-fit bug in the skeleton where fit_predict() was called twice
#      (producing inconsistent anomaly_score and is_anomaly pairs).
#
#   5. n_estimators=200 gives a smoother anomaly score surface over the default
#      100. Matters for Team 3 which ranks anomalies by score_samples() value.

import random
from datetime import datetime, timedelta
from typing import Dict

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

# ── Shared Constants (verbatim from README) ───────────────────────────────────
N_SAMPLES       = 500
CONTAMINATION   = 0.05
FEATURE_COLUMNS = ["cpu_percent", "memory_mb", "net_bytes_sent", "disk_read_ops"]


# ── Per-process baseline distributions ───────────────────────────────────────
# Calibrated from data/data.json.  Each key maps to kwargs used by the sampler.
#   cpu/mem  : normal distribution (loc, scale, clip lo/hi)
#   net      : exponential distribution (scale = mean), clipped at 12× scale
#   disk     : normal distribution (loc, scale, clip lo/hi)
#
# Why process-specific? Chrome's memory baseline is 600-1500 MB; svchost's is
# 50-500 MB.  A point at 3500 MB is 4σ from chrome's mean but ≈37σ from
# svchost's.  Process-aware baselines let IF exploit that variance difference.
PROCESS_PROFILES: Dict[str, dict] = {
    "chrome.exe": {
        # Scale reduced from 8→6 for tighter intra-class variance.
        # hi=50 leaves a ≥49-point gap to the cpu_spike floor of 99.
        "cpu":  dict(loc=20,   scale=6,   lo=1,   hi=50),
        "mem":  dict(loc=700,  scale=300, lo=200, hi=2000),
        "net":  dict(scale=60_000),
        "disk": dict(loc=80,   scale=40,  lo=0,   hi=500),
    },
    "docker.exe": {
        "cpu":  dict(loc=30,   scale=10,  lo=5,   hi=55),
        "mem":  dict(loc=1200, scale=400, lo=300, hi=2500),
        "net":  dict(scale=80_000),
        "disk": dict(loc=200,  scale=100, lo=0,   hi=600),
    },
    "python.exe": {
        "cpu":  dict(loc=18,   scale=8,   lo=0,   hi=50),
        "mem":  dict(loc=500,  scale=200, lo=100, hi=1500),
        "net":  dict(scale=10_000),
        "disk": dict(loc=100,  scale=60,  lo=0,   hi=500),
    },
    "git.exe": {
        "cpu":  dict(loc=8,    scale=4,   lo=0,   hi=28),
        "mem":  dict(loc=150,  scale=60,  lo=20,  hi=400),
        "net":  dict(scale=2_000),
        "disk": dict(loc=200,  scale=150, lo=0,   hi=700),
    },
    "code.exe": {
        "cpu":  dict(loc=25,   scale=8,   lo=2,   hi=48),
        "mem":  dict(loc=700,  scale=250, lo=200, hi=1500),
        "net":  dict(scale=5_000),
        "disk": dict(loc=120,  scale=60,  lo=0,   hi=500),
    },
    "svchost.exe": {
        "cpu":  dict(loc=5,    scale=3,   lo=0,   hi=16),
        "mem":  dict(loc=200,  scale=80,  lo=50,  hi=500),
        "net":  dict(scale=8_000),
        "disk": dict(loc=40,   scale=25,  lo=0,   hi=200),
    },
    "node.exe": {
        "cpu":  dict(loc=22,   scale=8,   lo=0,   hi=48),
        "mem":  dict(loc=350,  scale=150, lo=80,  hi=1000),
        "net":  dict(scale=30_000),
        "disk": dict(loc=60,   scale=30,  lo=0,   hi=300),
    },
    "explorer.exe": {
        "cpu":  dict(loc=3,    scale=2,   lo=0,   hi=12),
        "mem":  dict(loc=160,  scale=60,  lo=50,  hi=400),
        "net":  dict(scale=1_000),
        "disk": dict(loc=30,   scale=20,  lo=0,   hi=130),
    },
}

PROCESS_NAMES = list(PROCESS_PROFILES.keys())

# Frequency weights mirror real-world workstation process counts
_PROCESS_WEIGHTS = [0.20, 0.08, 0.18, 0.05, 0.15, 0.15, 0.10, 0.09]

# Anomaly catalogue with injection weights
# Four required types + two correlated patterns for multi-dimensional IF coverage
_ANOMALY_TYPES   = [
    "cpu_spike",        # isolated CPU: runaway process / cryptominer
    "memory_leak",      # extreme RSS: memory-leaking daemon
    "net_silence",      # high CPU + zero net: C2 beacon or ransomware
    "disk_storm",       # I/O flood: bulk encrypt/read
    "cpu_mem_burst",    # correlated CPU+mem: heavy cryptominer
    "disk_net_inversion",  # correlated disk+low-net: staging before exfil
]
_ANOMALY_WEIGHTS = [0.20, 0.20, 0.15, 0.15, 0.15, 0.15]


# ─────────────────────────────────────────────────────────────────────────────
# Private helpers
# ─────────────────────────────────────────────────────────────────────────────

def _sample_normal_row(process: str, rng: np.random.Generator) -> dict:
    """Return one set of feature values drawn from the process's normal profile."""
    p = PROCESS_PROFILES[process]
    return {
        "cpu_percent":    float(np.clip(rng.normal(p["cpu"]["loc"],  p["cpu"]["scale"]),
                                        p["cpu"]["lo"],  p["cpu"]["hi"])),
        "memory_mb":      float(np.clip(rng.normal(p["mem"]["loc"],  p["mem"]["scale"]),
                                        p["mem"]["lo"],  p["mem"]["hi"])),
        # Exponential gives a right-skewed network distribution — most processes
        # idle near 0, occasional bursts.  Clip at 12× mean to kill statistical noise.
        "net_bytes_sent": float(np.clip(rng.exponential(p["net"]["scale"]),
                                        0, p["net"]["scale"] * 12)),
        "disk_read_ops":  float(np.clip(rng.normal(p["disk"]["loc"], p["disk"]["scale"]),
                                        p["disk"]["lo"],  p["disk"]["hi"])),
    }


def _inject_anomaly(record: dict, atype: str, rng: np.random.Generator) -> None:
    """
    Mutate record's feature fields in-place to match the given anomaly signature.

    All injected values are chosen to sit well outside ANY process's normal hi
    bound, guaranteeing IF requires very few random splits to isolate them —
    which produces strongly negative score_samples() outputs.
    """
    if atype == "cpu_spike":
        # Floor at 99 makes injected cpu_spikes sit ≥44 pts above the max
        # normal ceiling (55). IsolationForest needs very few random cuts to
        # separate a point this far from the dense cluster → strong negative score.
        record["cpu_percent"] = float(rng.uniform(99, 100))

    elif atype == "memory_leak":
        record["memory_mb"] = float(rng.uniform(3500, 4096))

    elif atype == "net_silence":
        # CPU floor at 98; net=0 alone is common, so the extreme CPU is the
        # main detection signal. The joint rarity of (cpu>98, net=0) ensures
        # IsolationForest isolates this in very few random cuts.
        record["cpu_percent"]    = float(rng.uniform(98, 100))
        record["net_bytes_sent"] = 0.0

    elif atype == "disk_storm":
        # Floor raised to 950 — git.exe's normal ceiling is 700, so gap ≥ 250.
        record["disk_read_ops"] = float(rng.uniform(950, 1000))

    elif atype == "cpu_mem_burst":
        # Both dimensions simultaneously extreme — cryptominer signature.
        # CPU floor at 98 ensures joint (cpu>98, mem>3000) is extremely rare.
        record["cpu_percent"] = float(rng.uniform(98, 100))
        record["memory_mb"]   = float(rng.uniform(3000, 4096))

    elif atype == "disk_net_inversion":
        # Disk floor raised to 930 for the same gap reason as disk_storm.
        # Near-zero network + extreme disk = staging encrypted archive locally.
        record["disk_read_ops"]  = float(rng.uniform(930, 1000))
        record["net_bytes_sent"] = float(rng.uniform(0, 100))


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_process_data(n_samples: int = N_SAMPLES, _debug: bool = True) -> pd.DataFrame:
    """
    Generates synthetic process telemetry with realistic per-process distributions.
    Injects anomaly signatures into exactly 5% of rows before returning.

    Anomaly signatures injected (randomly weighted):
      - cpu_spike          : cpu_percent ∈ [99, 100]
      - memory_leak        : memory_mb   ∈ [3500, 4096]
      - net_silence        : net_bytes_sent = 0  AND  cpu_percent ∈ [98, 100]
      - disk_storm         : disk_read_ops ∈ [950, 1000]
      - cpu_mem_burst      : cpu_percent ∈ [98,100] AND memory_mb ∈ [3000,4096]
      - disk_net_inversion : disk_read_ops ∈ [930,1000] AND net_bytes_sent ∈ [0,100]

    Args:
        n_samples: Number of telemetry rows to generate.
        _debug:    Internal flag. When True, appends an `anomaly_type` column
                   (ground-truth label for testing/demo). Never set this in
                   production — Team 1/3 do not expect this column.

    Returns:
        pd.DataFrame with columns:
            timestamp, process_name, pid, cpu_percent,
            memory_mb, net_bytes_sent, disk_read_ops
        (NO anomaly_score or is_anomaly — those are added by run_anomaly_detection)
    """
    # Seed all RNG sources for full reproducibility
    np.random.seed(42)
    rng = np.random.default_rng(42)
    random.seed(42)

    base_time        = datetime.utcnow() - timedelta(minutes=n_samples)
    chosen_processes = random.choices(PROCESS_NAMES, weights=_PROCESS_WEIGHTS, k=n_samples)

    records = []
    for i in range(n_samples):
        proc   = chosen_processes[i]
        feats  = _sample_normal_row(proc, rng)
        record = {
            "timestamp":    base_time + timedelta(seconds=i * 6),
            "process_name": proc,
            "pid":          random.randint(1000, 65535),
            **feats,
            "anomaly_type": "normal",   # ground-truth label; stripped unless _debug=True
        }
        records.append(record)

    # Inject anomalies into exactly CONTAMINATION fraction of rows
    n_anomalies     = int(n_samples * CONTAMINATION)
    anomaly_indices = rng.choice(n_samples, size=n_anomalies, replace=False)
    anomaly_types   = random.choices(_ANOMALY_TYPES, weights=_ANOMALY_WEIGHTS, k=n_anomalies)

    for idx, atype in zip(anomaly_indices, anomaly_types):
        _inject_anomaly(records[idx], atype, rng)
        records[idx]["anomaly_type"] = atype

    df = pd.DataFrame(records)

    output_cols = ["timestamp", "process_name", "pid",
                   "cpu_percent", "memory_mb", "net_bytes_sent", "disk_read_ops"]
    if _debug:
        output_cols.append("anomaly_type")

    return df[output_cols]


def run_anomaly_detection(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fits an IsolationForest on FEATURE_COLUMNS of df.
    Appends two columns to df:
        anomaly_score : float  (raw score from score_samples(); more negative = more anomalous)
        is_anomaly    : bool   (True for the contamination fraction)

    n_estimators=200 (vs default 100) gives a smoother score surface, which
    improves the ranking quality used by Team 3's top-N selection.

    Returns:
        (df_all, df_anomalies)
        df_all       : full DataFrame with appended anomaly columns
        df_anomalies : filtered subset where is_anomaly == True, index reset
    """
    model = IsolationForest(
        n_estimators=200,    # smoother score surface → better score ranking for Team 3
        contamination=CONTAMINATION,
        random_state=42,
        max_samples="auto",  # auto = min(256, n_samples); sufficient for 500 rows
        n_jobs=-1,           # parallelise tree fitting across cores
    )

    X = df[FEATURE_COLUMNS].values

    # Single fit call; score_samples() and predict() share the same fitted state.
    # The skeleton's double fit_predict() call was both wasteful and produced
    # scores inconsistent with the is_anomaly flag.
    model.fit(X)

    df = df.copy()
    df["anomaly_score"] = model.score_samples(X)   # continuous severity ranking
    df["is_anomaly"]    = model.predict(X) == -1   # bool flag at contamination threshold

    df_anomalies = df[df["is_anomaly"]].reset_index(drop=True)
    return df, df_anomalies


# ─────────────────────────────────────────────────────────────────────────────
# Self-test entry point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    df = generate_process_data(_debug=True)
    df_all, df_anomalies = run_anomaly_detection(df)
    df_all["true_anomaly"] = df["anomaly_type"] != "normal"

    tp = (df_all["is_anomaly"] & df_all["true_anomaly"]).sum()
    fp = (df_all["is_anomaly"] & ~df_all["true_anomaly"]).sum()
    fn = (~df_all["is_anomaly"] & df_all["true_anomaly"]).sum()
    tn = (~df_all["is_anomaly"] & ~df_all["true_anomaly"]).sum()

    p = tp / (tp + fp) if (tp + fp) else 0
    r = tp / (tp + fn) if (tp + fn) else 0
    f1 = 2 * p * r / (p + r) if (p + r) else 0

    print(f"TP={tp}  FP={fp}  FN={fn}  TN={tn}")
    print(f"Precision={p:.4f}  Recall={r:.4f}  F1={f1:.4f}")
    print()

    for atype in sorted(df["anomaly_type"].unique()):
        if atype == "normal":
            continue
        n = (df["anomaly_type"] == atype).sum()
        caught = ((df["anomaly_type"] == atype) & df_all["is_anomaly"]).sum()
        print(f"  {atype:.<20s} {caught}/{n} ({caught/n:.0%})")
