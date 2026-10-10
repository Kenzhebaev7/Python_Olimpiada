ENTRIES = [
    {
        "keywords": ["input", "int(", "енгіз", "сан оқу", "ввод", "прочитать число"],
        "reply": {
            "kk": "input() әрқашан мәтін қайтарады. Сан керек болса int(input()) жазыңыз. Бір жолда бірнеше сан болса, split() арқылы бөліп, әрқайсын int() қылыңыз.",
            "ru": "input() всегда возвращает текст. Если нужно число, пишите int(input()). Несколько чисел в одной строке разделите через split() и каждое оберните в int().",
            "en": "input() always returns text. When you need a number, write int(input()). If one line has several numbers, split() it and wrap each piece in int().",
        },
    },
    {
        "keywords": ["range", "соңғы сан", "последнее число", "last number"],
        "reply": {
            "kk": "range(n) 0-ден n-ге дейін жүреді, бірақ n-нің өзі кірмейді. 1-ден n-ге дейін қосу керек болса, range(1, n + 1) қолданыңыз.",
            "ru": "range(n) идёт от 0 до n, но само n не входит. Чтобы пройти от 1 до n включительно, используйте range(1, n + 1).",
            "en": "range(n) runs from 0 up to but not including n. To include every number from 1 through n, use range(1, n + 1).",
        },
    },
    {
        "keywords": ["индекс", "тізім", "массив", "list", "index", "список", "массив"],
        "reply": {
            "kk": "Тізімнің бірінші элементі 0-индексте. Соңғы элементке -1 деп те қарауға болады. Индекс ұзындыққа тең болса, IndexError шығады.",
            "ru": "Первый элемент списка стоит на индексе 0. К последнему можно обратиться как -1. Если индекс равен длине списка, будет IndexError.",
            "en": "The first list item is at index 0. The last item is also index -1. An index equal to the length raises IndexError.",
        },
    },
    {
        "keywords": ["wa", "қате жауап", "wrong", "неверный ответ"],
        "reply": {
            "kk": "WA — бағдарлама аяқталды, бірақ шыққан жауап күткенмен сәйкес емес. Алдымен мысалды қолыңызбен есептеңіз, содан кейін print ішіндегі өрнекті сол есеппен салыстырыңыз.",
            "ru": "WA значит, что программа завершилась, но вывод не совпал с ожидаемым. Сначала посчитайте пример вручную, затем сравните выражение внутри print с этим расчётом.",
            "en": "WA means the program finished, but the output does not match. Work the sample by hand, then compare the expression inside print with that result.",
        },
    },
    {
        "keywords": ["return", "функци", "print", "функци", "function"],
        "reply": {
            "kk": "print мәнді экранға шығарады, бірақ функциядан нәтиже қайтармайды. Кейін сол мәнді қолданатын болсаңыз, return жазыңыз. Шығаруды функцияның сыртында қалдыруға болады.",
            "ru": "print показывает значение на экране, но не возвращает его из функции. Если значение нужно дальше, напишите return. Печать можно оставить снаружи функции.",
            "en": "print shows a value on screen, but it does not return that value from the function. If you need the value later, use return. Printing can stay outside the function.",
        },
    },
    {
        "keywords": ["шексіз", "тұрып қал", "tle", "бесконеч", "infinite", "timeout"],
        "reply": {
            "kk": "Цикл тоқтамаса, шарты ешқашан өзгермейді. while ішінде санағышты арттырыңыз немесе for қолданыңыз. Шексіз цикл уақыт шегіне тіреледі.",
            "ru": "Если цикл не останавливается, его условие никогда не меняется. Увеличивайте счётчик внутри while или используйте for. Бесконечный цикл упирается в лимит времени.",
            "en": "A loop that never stops has a condition that never changes. Increase a counter inside while, or use for. An infinite loop hits the time limit.",
        },
    },
    {
        "keywords": ["==", "тең бе", "шарт", " if", "if ", "условие", "condition"],
        "reply": {
            "kk": "Бір = меншіктейді, екі == салыстырады. if ішінде салыстыру керек. Бірнеше шартты and немесе or арқылы қосыңыз.",
            "ru": "Один знак = присваивает, два == сравнивают. Внутри if нужно сравнение. Несколько условий соединяйте через and или or.",
            "en": "One = assigns a value, two == compare values. Inside if you need a comparison. Join several conditions with and or or.",
        },
    },
    {
        "topic": "dp",
        "keywords": ["динамик", "динамическ", "dynamic", "мемоиз", "memo", "dp", "кестемен"],
        "hint": {
            "kk": "Ең кіші жағдайды алдымен толтырып, келесі ұяшықты сол дайын жауапқа сүйеңіз.",
            "ru": "Сначала заполните самый маленький случай, а следующую ячейку опирайте на уже готовый ответ.",
            "en": "Fill the smallest case first, then build the next cell from that saved answer.",
        },
        "reply": {
            "kk": "Динамикалық бағдарламалау қайталанатын кіші есепті бір рет шығарып, жауабын сақтап қояды. Алдымен ең кіші жағдайды толтырыңыз. Келесі ұяшық соның дайын жауабына сүйенсін. Бір есепті қайта-қайта рекурсиямен шығармаңыз: кесте немесе есте сақтау қолданыңыз.",
            "ru": "Динамическое программирование решает повторяющуюся подзадачу один раз и запоминает ответ. Сначала заполните самый маленький случай. Следующая ячейка должна опираться на уже готовый ответ. Не пересчитывайте одну и ту же задачу рекурсией: используйте таблицу или запоминание.",
            "en": "Dynamic programming solves a repeated smaller problem once and stores the answer. Fill the smallest case first. The next cell should use that saved answer. Do not recompute the same problem with plain recursion: use a table or memoization.",
        },
    },
    {
        "topic": "bsearch",
        "keywords": ["екілік іздеу", "бинарный", "binary search", "bsearch", "ортасы", "середина"],
        "hint": {
            "kk": "Тізім сұрыпталғанын тексеріңіз, содан кейін сол және оң шекараны ортасы арқылы тарылтыңыз.",
            "ru": "Проверьте, что список отсортирован, затем сужайте левую и правую границы через середину.",
            "en": "Check that the list is sorted, then narrow the left and right bounds using the middle.",
        },
        "reply": {
            "kk": "Екілік іздеу тек сұрыпталған тізімде дұрыс жұмыс істейді. Сол және оң шекараны ұстаңыз, ортасын алыңыз. Іздеген мән ортасынан кіші болса оң жақты тастаңыз, үлкен болса сол жақты. Шекаралар түйіскенде тоқтаңыз.",
            "ru": "Бинарный поиск работает только на отсортированном списке. Держите левую и правую границы и берите середину. Если искомое меньше середины, отбросьте правую часть, если больше — левую. Остановитесь, когда границы сойдутся.",
            "en": "Binary search only works on a sorted list. Keep a left and a right bound and take the middle. If the target is smaller than the middle, drop the right half; if it is larger, drop the left half. Stop when the bounds meet.",
        },
    },
    {
        "topic": "recursion",
        "keywords": ["рекурс", "recursion", "базалық", "базовый случай", "base case", "өзін шақыр", "вызывает себя"],
        "hint": {
            "kk": "Алдымен тоқтайтын базалық жағдайды жазыңыз, содан кейін есепті бір қадам кішірек шақырыңыз.",
            "ru": "Сначала напишите базовый случай, который останавливает вызовы, затем вызывайте задачу на один шаг меньше.",
            "en": "Write the base case that stops the calls first, then call the problem one step smaller.",
        },
        "reply": {
            "kk": "Рекурсия — функцияның өзін шақыруы. Алдымен тоқтайтын базалық жағдайды жазыңыз, мысалы n == 0 немесе тізім бос. Содан кейін есепті бір қадам кішірек бөлікке бөліңіз. База болмаса, шақырулар бітпей, бағдарлама тоқтайды.",
            "ru": "Рекурсия — это вызов функцией самой себя. Сначала напишите базовый случай, который останавливает вызовы, например n == 0 или пустой список. Затем разбейте задачу на часть на один шаг меньше. Без базы вызовы не закончатся и программа упадёт.",
            "en": "Recursion is a function calling itself. First write a base case that stops the calls, such as n == 0 or an empty list. Then split the problem into a piece one step smaller. Without a base case the calls never end and the program crashes.",
        },
    },
    {
        "topic": "loops",
        "keywords": ["цикл", "цикла", "loop", " for", "for ", "while", "итерац", "қайтала"],
        "hint": {
            "kk": "Цикл ішінде не өзгеретінін жазыңыз: санағыш, қосынды немесе келесі элемент.",
            "ru": "Внутри цикла явно меняйте то, от чего зависит остановка: счётчик, сумму или следующий элемент.",
            "en": "Inside the loop, change the thing the stop depends on: a counter, a sum, or the next item.",
        },
        "reply": {
            "kk": "Цикл бір әрекетті қайталайды. Неше рет білсеңіз for қолданыңыз, шартпен тоқтаса while. Ішінде не өзгеретінін жазыңыз: санағыш, қосынды немесе тізімдегі келесі элемент. Соңғы сан кірмей қалса, шекараны n емес n + 1 деп тексеріңіз.",
            "ru": "Цикл повторяет одно действие. Если число повторов известно, берите for; если остановка зависит от условия — while. Внутри должно меняться то, от чего зависит конец: счётчик, сумма или следующий элемент. Если последний номер не вошёл, проверьте границу n + 1, а не n.",
            "en": "A loop repeats one action. Use for when you know how many times, and while when a condition decides the stop. Inside, change what the ending depends on: a counter, a sum, or the next item. If the last number was left out, check the bound n + 1 rather than n.",
        },
    },
]

FALLBACK = {
    "kk": "Бұл сұрақты дәл таппадым. Цикл, рекурсия, екілік іздеу немесе динамикалық бағдарламалау туралы сұраңыз. Әзірге тексеріңіз: кіріс input() арқылы оқылды ма, жауап print() арқылы шықты ма, мысалды қолыңызбен есептедіңіз бе?",
    "ru": "Точного ответа на этот вопрос нет. Спросите про цикл, рекурсию, бинарный поиск или динамическое программирование. Пока проверьте: прочитан ли ввод через input(), выведен ли ответ через print() и посчитан ли пример вручную.",
    "en": "I do not have an exact answer for that question. Ask about loops, recursion, binary search, or dynamic programming. For now check whether input() read the data, print() wrote the answer, and you worked the sample by hand.",
}

EMPTY = {
    "kk": "Сұрақты қысқаша жазыңыз. Мысалы: рекурсия қалай тоқтайды?",
    "ru": "Напишите вопрос коротко. Например: как останавливается рекурсия?",
    "en": "Write a short question. For example: how does recursion stop?",
}


def _language(lang):
    from i18n import normalize_lang

    return normalize_lang(lang)


def _say(bucket, lang):
    language = _language(lang)
    return bucket.get(language) or bucket.get("kk") or ""


def _match(message):
    folded = (message or "").lower().replace("ё", "е")
    for item in ENTRIES:
        if any(word in folded for word in item["keywords"]):
            return item
    return None


def answer_question(message, lang="kk"):
    text = (message or "").strip()
    if not text:
        return _say(EMPTY, lang)
    item = _match(text)
    if item is None:
        return _say(FALLBACK, lang)
    return _say(item["reply"], lang)


def topic_hint(topic, lang="kk"):
    for item in ENTRIES:
        if item.get("topic") == topic and item.get("hint"):
            return _say(item["hint"], lang)
    return ""
