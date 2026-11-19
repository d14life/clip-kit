"""Fail unless a finished mp4 is mastered to SOUND-RULES.md: -14 +/-1 LUFS integrated, true peak <= -1 dBTP.

Run: python tools/scripts/mix_check.py out/final/<name>.mp4
"""

import re
import subprocess
import sys


def measure(path: str) -> tuple[float, float]:
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true",
                          "-f", "null", "-"], capture_output=True, text=True, check=True).stderr
    summary = err[err.rindex("Summary:"):]
    return (float(re.search(r"I:\s+(-?[\d.]+) LUFS", summary)[1]),
            float(re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", summary)[1]))


if __name__ == "__main__":
    lufs, peak = measure(sys.argv[1])
    ok = abs(lufs + 14) <= 1 and peak <= -1
    print(f"{'PASS' if ok else 'FAIL'}  integrated {lufs:.1f} LUFS (want -14 +/-1), true peak {peak:.1f} dBTP (want <= -1)")
    sys.exit(0 if ok else 1)
