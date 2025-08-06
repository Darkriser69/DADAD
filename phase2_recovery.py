import os
import subprocess
import csv
import magic
import hashlib
import argparse

RECOVERY_DIR = "recovered_files"
REPORT_FILE = "report.csv"

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True).decode("utf-8")
    except subprocess.CalledProcessError as e:
        print(f"[✘] Error running command: {cmd}")
        return ""

def get_partition_offset(image):
    mmls_output = run_cmd(f"mmls {image}")
    for line in mmls_output.splitlines():
        if line.strip().endswith("Linux"):  # or change based on FS
            return int(line.split()[2]) * 512
    return 0

def extract_deleted_entries(image, offset):
    fls_output = run_cmd(f"fls -rd -o {offset // 512} {image}")
    entries = []
    for line in fls_output.splitlines():
        if line.startswith('r'):  # deleted regular file
            parts = line.split(None, 2)
            if len(parts) < 3:
                continue
            meta = parts[1].strip(":")
            name = parts[2].strip()
            entries.append((meta, name))
    return entries

def recover_file(image, offset, meta, name):
    os.makedirs(RECOVERY_DIR, exist_ok=True)
    output_path = os.path.join(RECOVERY_DIR, f"{meta}_{name}")
    cmd = f"icat -o {offset // 512} {image} {meta} > \"{output_path}\""
    os.system(cmd)
    return output_path

def get_mime_and_extension(filepath):
    mime = magic.Magic(mime=True)
    file_mime = mime.from_file(filepath)
    ext = os.path.splitext(filepath)[1].lower()
    return file_mime, ext

def file_hash(filepath):
    try:
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(4096):
                hasher.update(chunk)
        return hasher.hexdigest()
    except:
        return ""

def generate_report(entries):
    with open(REPORT_FILE, "w", newline="") as csvfile:
        fieldnames = ["Meta", "Filename", "RecoveredPath", "Size(Bytes)", "SHA256", "DetectedType", "Extension", "Anomaly"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for meta, name in entries:
            filepath = recover_file(args.image, offset, meta, name)
            anomaly = []
            size = os.path.getsize(filepath)
            sha256 = file_hash(filepath)
            filetype, ext = get_mime_and_extension(filepath)

            if size == 0:
                anomaly.append("Corrupted (0B)")

            if filetype and ext not in filetype:
                anomaly.append("Extension Mismatch")

            # Compare hash of metadata name vs extension (rudimentary, simulated)
            if ext.replace('.', '') not in sha256:
                anomaly.append("Hash-Extension Mismatch")

            writer.writerow({
                "Meta": meta,
                "Filename": name,
                "RecoveredPath": filepath,
                "Size(Bytes)": size,
                "SHA256": sha256,
                "DetectedType": filetype,
                "Extension": ext,
                "Anomaly": "; ".join(anomaly) if anomaly else "None"
            })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 2: Deleted file recovery and metadata analysis")
    parser.add_argument("--image", required=True, help="Path to disk image")
    args = parser.parse_args()

    print("[+] Determining partition offset...")
    offset = get_partition_offset(args.image)

    print("[+] Scanning for deleted files...")
    entries = extract_deleted_entries(args.image, offset)

    print(f"[+] Found {len(entries)} deleted files. Recovering...")
    generate_report(entries)
    print(f"[✓] Report saved to {REPORT_FILE}")
