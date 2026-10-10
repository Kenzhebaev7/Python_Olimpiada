import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from i18n import text


def normalize(text):
    lines = (text or "").replace("\r\n", "\n").replace("\r", "\n").strip().split("\n")
    return "\n".join(line.rstrip() for line in lines)


def run_code(code, tests, timeout=2, lang="kk"):
    started = time.perf_counter()

    def finish(payload, runtime_ms=None):
        if runtime_ms is None:
            runtime_ms = int((time.perf_counter() - started) * 1000)
        payload["runtime_ms"] = int(runtime_ms)
        return payload

    source = (code or "").strip()
    if not source:
        return finish(
            {
                "verdict": "CE",
                "message": text("empty_code", lang),
                "error_log": text("empty_log", lang),
                "stderr": "",
                "actual": "",
                "expected": "",
            }
        )

    if len(source) > 20000:
        return finish(
            {
                "verdict": "CE",
                "message": text("long_code", lang),
                "error_log": text("long_log", lang),
                "stderr": "",
                "actual": "",
                "expected": "",
            }
        )

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "solution.py"
        path.write_text(source, encoding="utf-8")

        for index, test in enumerate(tests, start=1):
            try:
                env = os.environ.copy()
                env["PYTHONUTF8"] = "1"
                env["PYTHONIOENCODING"] = "utf-8"
                completed = subprocess.run(
                    [sys.executable, "-X", "utf8", "-I", str(path)],
                    input=test["input_data"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                    cwd=folder,
                    env=env,
                )
            except subprocess.TimeoutExpired:
                return finish(
                    {
                        "verdict": "TLE",
                        "message": text("tle", lang, index=index),
                        "error_log": text("tle_log", lang, timeout=timeout),
                        "stderr": "",
                        "actual": "",
                        "expected": "",
                    },
                    timeout * 1000,
                )

            stderr = (completed.stderr or "").strip()
            if completed.returncode != 0:
                verdict = "CE" if "SyntaxError" in stderr or "IndentationError" in stderr else "RE"
                return finish(
                    {
                        "verdict": verdict,
                        "message": text("runtime", lang) if verdict == "RE" else text("syntax", lang),
                        "error_log": stderr or text("crash_log", lang),
                        "stderr": stderr,
                        "actual": "",
                        "expected": "",
                    }
                )

            actual = normalize(completed.stdout)
            expected = normalize(test["output_data"])
            if actual != expected:
                return finish(
                    {
                        "verdict": "WA",
                        "message": text("wa", lang, index=index),
                        "error_log": text(
                            "wa_log",
                            lang,
                            input=test["input_data"],
                            expected=expected,
                            actual=actual,
                        ),
                        "stderr": "",
                        "actual": actual,
                        "expected": expected,
                    }
                )

    return finish(
        {
            "verdict": "AC",
            "message": text("ac", lang),
            "error_log": "",
            "stderr": "",
            "actual": "",
            "expected": "",
        }
    )
