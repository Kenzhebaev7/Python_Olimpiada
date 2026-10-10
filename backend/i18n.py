LANGS = ("kk", "ru", "en")

MESSAGES = {
    "empty_code": {
        "kk": "Код бос.",
        "ru": "Код пустой.",
        "en": "The code is empty.",
    },
    "empty_log": {
        "kk": "Алдымен шешімді жазыңыз.",
        "ru": "Сначала напишите решение.",
        "en": "Write a solution first.",
    },
    "long_code": {
        "kk": "Код тым ұзын.",
        "ru": "Код слишком длинный.",
        "en": "The code is too long.",
    },
    "long_log": {
        "kk": "Шешім 20000 таңбадан аспауы керек.",
        "ru": "Решение не должно быть длиннее 20000 символов.",
        "en": "The solution must stay under 20000 characters.",
    },
    "tle": {
        "kk": "{index}-тест уақыт шегінен асты.",
        "ru": "Тест {index} превысил лимит времени.",
        "en": "Test {index} exceeded the time limit.",
    },
    "tle_log": {
        "kk": "Лимит: {timeout} секунд.",
        "ru": "Лимит: {timeout} с.",
        "en": "Limit: {timeout} seconds.",
    },
    "runtime": {
        "kk": "Код орындалмады.",
        "ru": "Код не выполнился.",
        "en": "The program crashed.",
    },
    "syntax": {
        "kk": "Синтаксистік қате.",
        "ru": "Синтаксическая ошибка.",
        "en": "Syntax error.",
    },
    "crash_log": {
        "kk": "Бағдарлама қатемен аяқталды.",
        "ru": "Программа завершилась с ошибкой.",
        "en": "The program stopped with an error.",
    },
    "wa": {
        "kk": "{index}-тестте жауап қате.",
        "ru": "Неверный ответ на тесте {index}.",
        "en": "Wrong answer on test {index}.",
    },
    "wa_log": {
        "kk": "Кіріс:\n{input}\n\nКүтілген:\n{expected}\n\nСіздің жауабыңыз:\n{actual}",
        "ru": "Ввод:\n{input}\n\nОжидалось:\n{expected}\n\nВаш вывод:\n{actual}",
        "en": "Input:\n{input}\n\nExpected:\n{expected}\n\nYour output:\n{actual}",
    },
    "ac": {
        "kk": "Барлық тесттер қабылданды.",
        "ru": "Все тесты пройдены.",
        "en": "All tests passed.",
    },
    "ac_xp": {
        "kk": "Барлық тесттер қабылданды. +{xp} XP",
        "ru": "Все тесты пройдены. +{xp} XP",
        "en": "All tests passed. +{xp} XP",
    },
    "ac_again": {
        "kk": "Барлық тесттер қабылданды. Бұл есеп бұрын шешілген.",
        "ru": "Все тесты пройдены. Эта задача уже была решена.",
        "en": "All tests passed. This problem was already solved.",
    },
    "missing": {
        "kk": "Есеп табылмады.",
        "ru": "Задача не найдена.",
        "en": "Problem not found.",
    },
    "choice": {
        "kk": "Нұсқаны таңдаңыз.",
        "ru": "Выберите вариант.",
        "en": "Choose an option.",
    },
    "coach_indent": {
        "kk": "Жол басы шатасқан. if, for, while және def ішіндегі жолды 4 бос орынға ішке жылжытыңыз.",
        "ru": "Сбиты отступы. Строки внутри if, for, while и def сдвиньте на 4 пробела.",
        "en": "The indentation is off. Lines inside if, for, while, and def need 4 spaces.",
    },
    "coach_quote": {
        "kk": "Тырнақша немесе жақша жабылмай қалды.",
        "ru": "Не закрыты кавычки или скобка.",
        "en": "A quote or bracket was left unclosed.",
    },
    "coach_syntax": {
        "kk": "Синтаксистік қате. Қос нүктені, жақшаны және тырнақшаны тексеріңіз.",
        "ru": "Синтаксическая ошибка. Проверьте двоеточие, скобки и кавычки.",
        "en": "Syntax error. Check the colon, brackets, and quotes.",
    },
    "coach_tle": {
        "kk": "Бағдарлама тым ұзақ жүрді. Цикл шарты ешқашан өзгермей ме, соны тексеріңіз.",
        "ru": "Программа работала слишком долго. Проверьте, меняется ли условие цикла.",
        "en": "The program ran too long. Check whether the loop condition ever changes.",
    },
    "coach_value": {
        "kk": "Сан күткен жерде басқа нәрсе келді. input() мәтін береді, сан керек болса int() қолданыңыз.",
        "ru": "Там, где ждали число, пришло другое. input() даёт текст, для числа нужен int().",
        "en": "Something other than a number arrived. input() returns text, so use int() when you need a number.",
    },
    "coach_type": {
        "kk": "Жолды санмен салыстырып немесе қосып жатырсыз. input() нәтижесін int() қылыңыз.",
        "ru": "Строка сравнивается или складывается с числом. Оберните результат input() в int().",
        "en": "A string is being compared or added to a number. Wrap input() with int().",
    },
    "coach_name": {
        "kk": "Мұндай айнымалы жоқ. Атын дәл жазғаныңызды және оны бұрын құрғаныңызды тексеріңіз.",
        "ru": "Такой переменной нет. Проверьте имя и что она создана раньше.",
        "en": "That name is not defined. Check the spelling and that you created it first.",
    },
    "coach_index": {
        "kk": "Тізімде жоқ орынды сұрадыңыз. Индекс 0-ден басталады және ұзындықтан кіші болуы керек.",
        "ru": "Запрошен несуществующий индекс. Индексы начинаются с 0 и должны быть меньше длины.",
        "en": "That index is outside the list. Indexes start at 0 and must be smaller than the length.",
    },
    "coach_zero": {
        "kk": "Нөлге бөлдіңіз. Бөлмес бұрын бөлінгіштің 0 емес екенін тексеріңіз.",
        "ru": "Деление на ноль. Перед делением проверьте, что делитель не 0.",
        "en": "Division by zero. Check that the divisor is not 0.",
    },
    "coach_crash": {
        "kk": "Бағдарлама қатемен тоқтады. Төмендегі қызыл жолдағы қате түрін оқыңыз.",
        "ru": "Программа остановилась с ошибкой. Прочитайте тип ошибки в красной строке ниже.",
        "en": "The program stopped with an error. Read the error type in the red line below.",
    },
    "coach_blank": {
        "kk": "Ештеңе шықпады. Жауапты print() арқылы шығарыңыз.",
        "ru": "Ничего не выведено. Напечатайте ответ через print().",
        "en": "Nothing was printed. Output the answer with print().",
    },
    "coach_offby": {
        "kk": "Жауап бірге ғана қате. Цикл шегі range(n) пе, әлде range(n + 1) пе, соны тексеріңіз.",
        "ru": "Ответ отличается на единицу. Проверьте границу цикла: range(n) или range(n + 1).",
        "en": "The answer is off by one. Check whether the loop is range(n) or range(n + 1).",
    },
    "coach_case": {
        "kk": "Әріптердің үлкен-кішісі басқа. Шығаруды есептегідей жазыңыз.",
        "ru": "Отличается регистр букв. Напишите вывод точно как в условии.",
        "en": "The letter case does not match. Print the output exactly as the statement asks.",
    },
    "coach_lines": {
        "kk": "Жол саны сәйкес емес. Әр жауапты жеке print қылыңыз немесе бәрін бір жолға жинаңыз.",
        "ru": "Число строк не совпало. Печатайте каждый ответ отдельно или соберите всё в одну строку.",
        "en": "The number of lines does not match. Print each answer on its own line, or keep them on one line.",
    },
    "coach_input": {
        "kk": "Кірісті оқымадыңыз. Сандарды кодқа жазып қоймай, input() арқылы алыңыз.",
        "ru": "Ввод не прочитан. Берите числа через input(), а не записывайте их в код.",
        "en": "You did not read the input. Use input() instead of hard-coding the numbers.",
    },
    "coach_generic": {
        "kk": "Шыққан жауап күткенмен сәйкес емес. Мысалды қолыңызбен есептеп, print ішіндегі өрнекті тексеріңіз.",
        "ru": "Вывод не совпал с ожидаемым. Посчитайте пример вручную и проверьте выражение внутри print.",
        "en": "The output does not match. Work the sample by hand and check the expression inside print.",
    },
    "lead_WA": {
        "kk": "Нәтиже қате (WA).",
        "ru": "Ответ неверный (WA).",
        "en": "Wrong answer (WA).",
    },
    "lead_TLE": {
        "kk": "Уақыт шегінен асып кетті (TLE).",
        "ru": "Превышен лимит времени (TLE).",
        "en": "Time limit exceeded (TLE).",
    },
    "lead_RE": {
        "kk": "Бағдарлама қатемен тоқтады (RE).",
        "ru": "Программа остановилась с ошибкой (RE).",
        "en": "The program crashed (RE).",
    },
    "lead_CE": {
        "kk": "Синтаксистік қате (CE).",
        "ru": "Синтаксическая ошибка (CE).",
        "en": "Syntax error (CE).",
    },
    "lead_AC": {
        "kk": "Жауап қабылданды (AC).",
        "ru": "Ответ принят (AC).",
        "en": "Accepted (AC).",
    },
    "hint_1": {
        "kk": "💡 Есептің шартына қайта қараңыз: Енгізілген мәліметтер типтері мен шектеулеріне назар аударыңыз.",
        "ru": "💡 Перечитайте условие: обратите внимание на типы данных и ограничения.",
        "en": "💡 Reread the statement: look at the input types and the limits.",
    },
    "hint_2": {
        "kk": "🔍 Индексті тексеріңіз: Цикл ішінде тізім шекарасынан шығып кету (IndexError) немесе шексіз цикл болмағанын зерттеңіз.",
        "ru": "🔍 Проверьте индексы: нет ли выхода за границу списка (IndexError) или бесконечного цикла.",
        "en": "🔍 Check indexes: look for an IndexError past the end of a list, or a loop that never stops.",
    },
    "hint_3": {
        "kk": "⚠️ Шеткі жағдай (Edge Case): Енгізу бос болғанда немесе теріс сан берілгенде код қалай жұмыс істейді?",
        "ru": "⚠️ Граничный случай: что делает код, если ввод пустой или число отрицательное?",
        "en": "⚠️ Edge case: what happens when the input is empty or a number is negative?",
    },
    "advice": {
        "kk": "Бүгін {topic} тақырыбын қайталауды ұсынамын!",
        "ru": "Сегодня советую повторить тему «{topic}».",
        "en": "Today I suggest reviewing {topic}.",
    },
    "advice_done": {
        "kk": "Барлық тақырып жабық. Ескі есепті қайта шешіп, жылдамдықты бекітіңіз.",
        "ru": "Все темы закрыты. Перерешайте старую задачу и закрепите скорость.",
        "en": "Every topic is complete. Re-solve an old problem and lock in your speed.",
    },
    "reason": {
        "kk": "Ең әлсіз тақырып: {title}. Осы тақырыпта {solved}/{total}.",
        "ru": "Самая слабая тема: {title}. В ней решено {solved}/{total}.",
        "en": "Weakest topic: {title}. Solved {solved}/{total} there.",
    },
}


def normalize_lang(value):
    code = str(value or "kk").strip().lower().replace("_", "-").split("-")[0]
    return code if code in LANGS else "kk"


def current_lang():
    try:
        from flask import has_request_context, request
    except ImportError:
        return "kk"
    if not has_request_context():
        return "kk"
    return normalize_lang(request.headers.get("X-Lang") or request.args.get("lang"))


def text(key, lang="kk", **kwargs):
    bucket = MESSAGES.get(key, {})
    template = bucket.get(normalize_lang(lang)) or bucket.get("kk") or key
    return template.format(**kwargs) if kwargs else template
