import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

MAX_STEPS = 70

RUNNER = r"""
import json
import os
import sys

target = os.path.normcase(os.path.abspath(sys.argv[1]))
steps_path = sys.argv[2]
max_steps = int(sys.argv[3])
steps = []
stdout_chunks = []
last_line = {}
truncated = False


class Capture:
    def write(self, text):
        stdout_chunks.append(text)

    def flush(self):
        pass


def shorten(value):
    try:
        text = repr(value)
    except Exception:
        text = "?"
    if len(text) > 80:
        return text[:77] + "..."
    return text


def snapshot(frame):
    data = {}
    for key, value in frame.f_locals.items():
        if key.startswith("__"):
            continue
        data[key] = shorten(value)
        if len(data) >= 12:
            break
    return data


def dump(error=""):
    payload = {
        "steps": steps,
        "stdout": "".join(stdout_chunks)[-500:],
        "error": error,
        "truncated": truncated or len(steps) >= max_steps,
    }
    with open(steps_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)


def remember(frame, line):
    global truncated
    if len(steps) >= max_steps:
        truncated = True
        return
    steps.append(
        {
            "line": line,
            "locals": snapshot(frame),
            "stdout": "".join(stdout_chunks)[-240:],
        }
    )
    dump()


def tracer(frame, event, arg):
    if os.path.normcase(os.path.abspath(frame.f_code.co_filename)) != target:
        return tracer
    key = id(frame)
    if event == "line":
        if key in last_line:
            remember(frame, last_line[key])
        last_line[key] = frame.f_lineno
    elif event == "return" and key in last_line:
        remember(frame, last_line.pop(key))
    return tracer


sys.stdout = Capture()
error = ""
try:
    source = open(target, encoding="utf-8").read()
    compiled = compile(source, target, "exec")
    sys.settrace(tracer)
    exec(compiled, {"__name__": "__main__"})
except SyntaxError as exc:
    error = f"SyntaxError: {exc.msg} (жол {exc.lineno})"
except Exception as exc:
    error = f"{type(exc).__name__}: {exc}"
finally:
    sys.settrace(None)
    sys.stdout = sys.__stdout__
    dump(error)
"""


def trace_code(code, stdin_text="", timeout=2):
    source = (code or "").strip()
    if not source:
        return {"steps": [], "stdout": "", "error": "Код бос.", "truncated": False, "stdin": ""}
    if len(source) > 20000:
        return {"steps": [], "stdout": "", "error": "Код тым ұзын.", "truncated": False, "stdin": ""}

    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        solution = root / "solution.py"
        runner = root / "runner.py"
        steps_path = root / "steps.json"
        solution.write_text(code or "", encoding="utf-8")
        runner.write_text(RUNNER, encoding="utf-8")
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            completed = subprocess.run(
                [sys.executable, "-X", "utf8", "-I", str(runner), str(solution), str(steps_path), str(MAX_STEPS)],
                input=stdin_text or "",
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                cwd=folder,
                env=env,
            )
        except subprocess.TimeoutExpired:
            partial = _read_steps(steps_path)
            partial["error"] = partial.get("error") or "Бағдарлама тым ұзақ жүрді. Цикл шегін тексеріңіз."
            partial["stdin"] = stdin_text or ""
            partial["truncated"] = True
            return partial

        payload = _read_steps(steps_path)
        if not steps_path.exists():
            stderr = (completed.stderr or "").strip()
            payload["error"] = stderr or "Қадамдарды оқу мүмкін болмады."
        payload["stdin"] = stdin_text or ""
        return payload


def _read_steps(path):
    if not path.exists():
        return {"steps": [], "stdout": "", "error": "", "truncated": False}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"steps": [], "stdout": "", "error": "Қадамдар файлы бұзылған.", "truncated": False}
    data.setdefault("steps", [])
    data.setdefault("stdout", "")
    data.setdefault("error", "")
    data.setdefault("truncated", False)
    return data
