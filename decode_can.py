#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import cantools
import pandas as pd
import re
import binascii
from collections import Counter


def parse_log_line(line):
    """Parse a line from candump: (timestamp) iface ID#DATA"""
    m = re.match(r"\(([\d\.]+)\)\s+\S+\s+([0-9A-Fa-f]+)#([0-9A-Fa-f]*)", line)
    if not m:
        return None

    timestamp = float(m.group(1))
    can_id = int(m.group(2), 16)
    data_str = m.group(3)

    if len(data_str) % 2 != 0:
        return None

    data = binascii.unhexlify(data_str) if data_str else b""
    return timestamp, can_id, data_str, data


def decode_can(logfile, dbcfile):
    db = cantools.database.load_file(dbcfile)
    dbc_messages = {msg.frame_id: msg for msg in db.messages}

    rows = []
    dlc_adjustments = []
    decode_errors = []

    total_messages = 0
    per_id_counts = Counter()
    per_id_decoded = Counter()
    per_id_dlc_corrections = Counter()

    with open(logfile, "r") as f:
        for line in f:
            parsed = parse_log_line(line)
            if not parsed:
                continue

            total_messages += 1
            timestamp, can_id, data_str, data = parsed
            per_id_counts[can_id] += 1

            msg = dbc_messages.get(can_id)
            if msg is None:
                continue

            actual_len = len(data)
            expected_len = msg.length

            if actual_len != expected_len:
                if actual_len < expected_len:
                    data = data + b"\x00" * (expected_len - actual_len)
                else:
                    data = data[:expected_len]

                dlc_adjustments.append({
                    "timestamp": timestamp,
                    "can_id": can_id,
                    "actual_len": actual_len,
                    "expected_len": expected_len,
                    "original_hex": data_str.lower(),
                    "adjusted_hex": data.hex()
                })
                per_id_dlc_corrections[can_id] += 1

            try:
                decoded = msg.decode(data)
                if decoded:
                    decoded["timestamp"] = timestamp
                    rows.append(decoded)
                    per_id_decoded[can_id] += 1
            except Exception as e:
                decode_errors.append((timestamp, can_id, str(e)))

    df = pd.DataFrame(rows)
    total_decoded_messages = len(df)
    total_signals = df.shape[1] - 1 if not df.empty else 0
    return (df, dlc_adjustments, decode_errors,
            total_messages, total_decoded_messages, total_signals,
            per_id_counts, per_id_decoded, per_id_dlc_corrections)


def wide_format(df):
    """Wide CSV → one column per signal"""
    return df.sort_values("timestamp").reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(
        description="CAN log decoder using DBC → Wide CSV with statistics"
    )
    parser.add_argument("--log", required=True, help="CAN log file (candump format)")
    parser.add_argument("--dbc", required=True, help="DBC file")
    parser.add_argument("--out", default="decoded.csv", help="Output CSV file")

    args = parser.parse_args()

    print(f"[INFO] Loading DBC file: {args.dbc}")
    print(f"[INFO] Reading CAN log file: {args.log}")

    (df, dlc_adjustments, decode_errors,
     total_msgs, decoded_msgs, total_signals,
     per_id_counts, per_id_decoded, per_id_dlc_corrections) = decode_can(args.log, args.dbc)

    print("[INFO] Generating DataFrame…")
    df_wide = wide_format(df)
    df_wide.to_csv(args.out, index=False)
    print(f"[INFO] Done! CSV exported to: {args.out}")

    # Summary and per-CAN-ID statistics
    print("\n===== SUMMARY =====")
    print(f"  Total CAN messages in log: {total_msgs}")
    print(f"  Total messages decoded (found in DBC): {decoded_msgs}")
    print(f"  Total signals decoded: {total_signals}\n")

    print("Per-CAN-ID statistics:")
    print(f"{'CAN-ID':>8} | {'Total Msgs':>10} | {'Decoded':>8} | {'DLC Corrected':>13}")
    print("-"*50)
    for cid in sorted(per_id_counts):
        total = per_id_counts[cid]
        decoded = per_id_decoded.get(cid, 0)
        dlc_corr = per_id_dlc_corrections.get(cid, 0)
        print(f"0x{cid:06X} | {total:10} | {decoded:8} | {dlc_corr:13}")

    # DLC-adjustment overview
    if dlc_adjustments:
        print("\nDLC adjustments (compressed overview):")
        dlc_by_id = {}
        for adj in dlc_adjustments:
            cid = adj['can_id']
            if cid not in dlc_by_id:
                dlc_by_id[cid] = []
            dlc_by_id[cid].append(adj)

        for cid, adj_list in sorted(dlc_by_id.items()):
            first = adj_list[0]
            count = len(adj_list)
            print(f"  CAN-ID 0x{cid:X}: {count} messages corrected, first example:")
            print(f"    Timestamp: {first['timestamp']}")
            print(f"    DLC: {first['actual_len']} → {first['expected_len']}")
            print(f"    Original: {first['original_hex']}")
            print(f"    Adjusted: {first['adjusted_hex']}")

    # Decoding errors
    if decode_errors:
        print("\nDecoding errors (after DLC adjustment):")
        for ts, cid, err in decode_errors[:30]:
            print(f"  {ts}: 0x{cid:X} - {err}")

    print("===== END INFO =====")


if __name__ == "__main__":
    main()
