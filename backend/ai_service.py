import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

from tutor import answer_question

LEVEL_TEXT = {
    1: "💡 Есептің шартына қайта қараңыз: Енгізілген мәліметтер типтері мен шектеулеріне назар аударыңыз.",
    2: "🔍 Индексті тексеріңіз: Цикл ішінде тізім шекарасынан шығып кету (IndexError) немесе шексіз цикл болмағанын зерттеңіз.",
    3: "⚠️ Шеткі жағдай (Edge Case): Енгізу бос болғанда немесе теріс сан берілгенде код қалай жұмыс істейді?",
}

VERDICT_LEAD = {
    "WA": "Нәтиже қате (WA).",
    "TLE": "Уақыт шегінен асып кетті (TLE).",
    "RE": "Бағдарлама қатемен тоқтады (RE).",
    "CE": "Синтаксистік қате (CE).",
    "AC": "Жауап қабылданды (AC).",
}

PLACEHOLDERS = {
    "",
    "changeme",
    "your-key",
    "your_key",
    "sk-xxx",
    "sk-your-key",
    "none",
    "null",
    "undefined",
}


def load_env_file():
    path = Path(__file__).resolve().parent / ".env"
    if not path.exists():
        return
    try:
        from dotenv import load_dotenv

        load_dotenv(path)
        return
    except ImportError:
        pass
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def configured_key():
    load_env_file()
    key = os.environ.get("OPENAI_API_KEY", "").strip().strip('"').strip("'")
    if key.lower() in PLACEHOLDERS:
        return ""
    if not key.startswith("sk-") or len(key) < 20:
        return ""
    return key


def _mock_scaffold(verdict, level, lang="kk"):
    from i18n import text

    code = (verdict or "WA").upper()
    lead_key = f"lead_{code}" if code in ("WA", "TLE", "RE", "CE", "AC") else "lead_WA"
    return f"{text(lead_key, lang)} {text(f'hint_{level if level in (1, 2, 3) else 1}', lang)}"


def _openai_chat(messages):
    key = configured_key()
    if not key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=key, timeout=20)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=messages,
        )
        content = response.choices[0].message.content
        return (content or "").strip() or None
    except ImportError:
        return _openai_http(key, messages)
    except Exception as exc:
        status = getattr(exc, "status_code", None)
        name = exc.__class__.__name__.lower()
        if status in (401, 403) or "auth" in name or "auth" in str(exc).lower():
            return None
        return None


def _openai_http(key, messages):
    payload = json.dumps(
        {"model": "gpt-4o-mini", "temperature": 0.4, "messages": messages}
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        return (data["choices"][0]["message"]["content"] or "").strip() or None
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            return None
        return None
    except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError, OSError):
        return None


def _complete(messages, mock_text):
    if configured_key():
        text = _openai_chat(messages)
        if text:
            return {"text": text, "source": "openai"}
    time.sleep(0.5)
    return {"text": mock_text, "source": "mock"}


def scaffold_reply(verdict, level, title, statement, lang="kk", topic=None):
    from i18n import normalize_lang
    from tutor import topic_hint

    language = {"kk": "Kazakh", "ru": "Russian", "en": "English"}.get(normalize_lang(lang), "Kazakh")
    mock = _mock_scaffold(verdict, level, lang)
    extra = topic_hint(topic, lang)
    if extra:
        mock = f"{mock}\n{extra}"
    messages = [
        {
            "role": "system",
            "content": (
                f"You tutor a student for a Python olympiad. Reply in {language}, 2-3 sentences. "
                "Do not give the full solution code. Push the student to think."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Есеп: {title}\nШарт: {statement[:500]}\n"
                f"Вердикт: {verdict}. Кеңес деңгейі: {level} (1 жеңіл сұрақ, 2 логика, 3 шеткі жағдай)."
            ),
        },
    ]
    return _complete(messages, mock)


def tutor_reply(message, lang=None):
    from i18n import current_lang, normalize_lang

    language = normalize_lang(lang or current_lang())
    spoken = {"kk": "Kazakh", "ru": "Russian", "en": "English"}.get(language, "Kazakh")
    mock = answer_question(message, language)
    messages = [
        {
            "role": "system",
            "content": (
                f"You tutor a student for a Python olympiad. Reply in {spoken}, 2-4 sentences. "
                "Do not give a full solution."
            ),
        },
        {"role": "user", "content": message or ""},
    ]
    return _complete(messages, mock)


def parent_reply(name, weekly_xp, streak, strength, weakness):
    mock = (
        f"{name} осы аптада {weekly_xp} XP жинады. Серия: {streak} күн. "
        f"Күшті жағы: {strength}. Әлсіз жағы: {weakness}. "
        "Әлсіз тақырыптан бір оңай есепті бірге қайталаңыз."
    )
    messages = [
        {
            "role": "system",
            "content": "Ата-анаға арналған қысқа есеп жаз. Қазақша, жылы, кодсыз.",
        },
        {"role": "user", "content": mock},
    ]
    return _complete(messages, mock)


def draft_reply(topic, difficulty, note):
    mock_body = {
        "title": f"{topic} бойынша жаттығу",
        "statement": (
            f"Оқушыға {difficulty} деңгейіндегі {topic} есебін беріңіз. "
            "Кірістен бүтін сан оқып, шарт бойынша бір сан шығарыңыз. "
            f"Мұғалім ескертпесі: {note or 'жоқ'}."
        ),
        "starter_code": "n = int(input())\n",
        "sample_input": "4\n",
        "sample_output": "4\n",
    }
    messages = [
        {
            "role": "system",
            "content": (
                "Python олимпиада есебінің жобасын JSON қылып қайтар: "
                "title, statement, starter_code, sample_input, sample_output. "
                "Мәтін қазақша. Толық шешімді қоспа."
            ),
        },
        {
            "role": "user",
            "content": f"Тақырып: {topic}. Қиындық: {difficulty}. Ескертпе: {note or 'жоқ'}.",
        },
    ]
    if configured_key():
        text = _openai_chat(messages)
        parsed = _parse_draft(text) if text else None
        if parsed:
            parsed["source"] = "openai"
            return parsed
    time.sleep(0.5)
    mock_body["source"] = "mock"
    return mock_body


def _parse_draft(text):
    if not text:
        return None
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw[: raw.rfind("```")]
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            return None
        try:
            data = json.loads(raw[start : end + 1])
        except json.JSONDecodeError:
            return None
    title = str(data.get("title") or "").strip()
    statement = str(data.get("statement") or "").strip()
    if not title or not statement:
        return None
    return {
        "title": title[:120],
        "statement": statement[:2000],
        "starter_code": str(data.get("starter_code") or "n = int(input())\n")[:2000],
        "sample_input": str(data.get("sample_input") or "1\n")[:500],
        "sample_output": str(data.get("sample_output") or "1\n")[:500],
    }
