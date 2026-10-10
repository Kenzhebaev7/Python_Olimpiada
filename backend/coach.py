def _is_int(text):
    try:
        int(text)
        return True
    except (TypeError, ValueError):
        return False


def explain(verdict, stderr, actual, expected, code, coach_hint, lang="kk"):
    from i18n import text
    blob = f"{stderr or ''}\n{code or ''}".lower()
    hint = (coach_hint or "").strip()

    if verdict == "CE":
        if "indentationerror" in blob or "unexpected indent" in blob:
            return text("coach_indent", lang)
        if "eol while scanning" in blob or "unterminated" in blob:
            return text("coach_quote", lang)
        return text("coach_syntax", lang)

    if verdict == "TLE":
        return text("coach_tle", lang)

    if verdict == "RE":
        if "valueerror" in blob:
            return text("coach_value", lang)
        if "typeerror" in blob and "str" in blob and "int" in blob:
            return text("coach_type", lang)
        if "nameerror" in blob:
            return text("coach_name", lang)
        if "indexerror" in blob:
            return text("coach_index", lang)
        if "zerodivisionerror" in blob:
            return text("coach_zero", lang)
        return text("coach_crash", lang)

    if verdict != "WA":
        return ""

    notes = []
    actual_text = actual or ""
    expected_text = expected or ""
    source = code or ""

    if actual_text == "":
        notes.append(text("coach_blank", lang))
    elif _is_int(actual_text) and _is_int(expected_text) and abs(int(actual_text) - int(expected_text)) == 1:
        notes.append(text("coach_offby", lang))
    elif actual_text.lower() == expected_text.lower() and actual_text != expected_text:
        notes.append(text("coach_case", lang))
    elif expected_text.count("\n") != actual_text.count("\n"):
        notes.append(text("coach_lines", lang))

    if "input(" not in source:
        notes.append(text("coach_input", lang))
    if hint:
        notes.append(hint)
    if not notes:
        notes.append(text("coach_generic", lang))
    return " ".join(notes[:2])
