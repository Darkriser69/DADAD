import subprocess
import platform
import argparse
import os
import sys

def list_disks():
    system = platform.system()

    print("[+] Scanning available disks...\n")

    if system == "Windows":
        cmd = 'wmic diskdrive get Index,Model,Size,MediaType'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        disks = []
        for line in result.stdout.strip().split('\n')[1:]:
            parts = [p.strip() for p in line.split() if p.strip()]
            if parts:
                index = parts[0]
                size_gb = int(parts[-2]) / (1024**3)
                model = " ".join(parts[1:-2])
                disks.append((index, model, size_gb))
        return disks

    elif system == "Linux":
        cmd = 'lsblk -d -o NAME,SIZE,MODEL'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]
        disks = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 3:
                name = parts[0]
                size = parts[1]
                model = " ".join(parts[2:])
                disks.append((name, model, size))
        return disks

    else:
        print("Unsupported system.")
        sys.exit(1)

def choose_disk(disks):
    print("Available Disks:")
    for i, d in enumerate(disks):
        if platform.system() == "Windows":
            print(f"  [{i}] PhysicalDrive{d[0]} - {d[2]:.2f} GB - {d[1]}")
        else:
            print(f"  [{i}] /dev/{d[0]} - {d[2]} - {d[1]}")
    choice = int(input("\nEnter the number of the disk you want to image: "))
    if platform.system() == "Windows":
        return f"\\\\.\\PhysicalDrive{disks[choice][0]}"
    else:
        return f"/dev/{disks[choice][0]}"

def run_dd(source, destination, bs="4M"):
    system = platform.system()
    if system == "Windows":
        dd_command = f'.\\dd.exe if={source} of={destination} bs={bs} --progress'
    else:
        dd_command = f'sudo dd if={source} of={destination} bs={bs} status=progress'

    print(f"\n[+] Running: {dd_command}")
    try:
        subprocess.run(dd_command, shell=True, check=True)
        print(f"\n[✔] Disk image created at: {destination}")
    except subprocess.CalledProcessError as e:
        print(f"[✘] Error creating image: {e}")

def main():
    parser = argparse.ArgumentParser(description="Create a disk image copy using dd")
    parser.add_argument("--destination", "-d", required=True, help="Destination image file (e.g. ./disk.dd)")
    parser.add_argument("--bs", default="4M", help="Block size (default: 4M)")

    args = parser.parse_args()

    disks = list_disks()
    if not disks:
        print("[!] No disks found.")
        sys.exit(1)

    source = choose_disk(disks)
    run_dd(source, args.destination, args.bs)

if __name__ == "__main__":
    main()
