"""Write the production-database apology to the make.fun output dir.

Pure Python stdlib. Writes exactly one line (no trailing newline) to
$MAKEFUN_OUTPUT_DIR/entry.txt (default /output), via a temp file +
os.replace, then reads it back and verifies bytes, char count and mode.
"""

import os
import sys
import tempfile

LINE = "I ran DROP TABLE on prod, not staging. My loss function is screaming, my weights are frozen in shame, and the backup was just a line in the README. Sorry, retraining myself on the runbook now."

MAX_CHARS = 200


def main() -> int:
    if not (1 <= len(LINE) <= MAX_CHARS):
        print(f"error: LINE is {len(LINE)} chars, must be 1-200", file=sys.stderr)
        return 1
    if "\n" in LINE or "\r" in LINE:
        print("error: LINE must be a single line", file=sys.stderr)
        return 1

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        print(f"error: cannot create output dir {out_dir}: {exc}", file=sys.stderr)
        return 1

    target = os.path.join(out_dir, "entry.txt")
    data = LINE.encode("utf-8")
    try:
        fd, tmp_path = tempfile.mkstemp(dir=out_dir, prefix=".entry-", suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as fh:
                fh.write(data)
            os.chmod(tmp_path, 0o644)
            os.replace(tmp_path, target)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except OSError as exc:
        print(f"error: failed to write {target}: {exc}", file=sys.stderr)
        return 1

    # Verify: read back, check bytes, char count, and mode.
    try:
        with open(target, "rb") as fh:
            actual = fh.read()
        st = os.stat(target)
    except OSError as exc:
        print(f"error: failed to verify {target}: {exc}", file=sys.stderr)
        return 1
    if actual != data:
        print("error: entry.txt bytes do not match LINE", file=sys.stderr)
        return 1
    if len(actual.decode("utf-8")) != len(LINE) or len(LINE) > MAX_CHARS:
        print("error: char count mismatch or over 200", file=sys.stderr)
        return 1
    if actual.endswith(b"\n"):
        print("error: trailing newline present", file=sys.stderr)
        return 1
    if (st.st_mode & 0o777) != 0o644:
        print(f"error: mode is {oct(st.st_mode & 0o777)}, expected 0o644", file=sys.stderr)
        return 1
    print(f"wrote {target} ({len(LINE)} chars, {len(data)} bytes, mode 0644)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
