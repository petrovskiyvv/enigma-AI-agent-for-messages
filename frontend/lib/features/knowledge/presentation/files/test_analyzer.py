"""
Юнит-тесты: app/services/analyzer.py — класс TextAnalyzer

Покрытие:
  analyze_tone       — негатив / позитив / нейтраль / пустая строка / регистр
  classify_category  — все 4 категории / регистр / пустая строка
  extract_devices    — зав.номер / серийный паттерн / несколько / пусто / email не попадает
  extract_email      — стандарт / точки / пусто / в середине текста
  extract_phone      — +7 / 8 / пусто / в предложении
  extract_name       — "с уважением" / "меня зовут" / без имени / с отчеством
  summarize          — короткий / длинный (>100) / многопредложный / ровно 100 символов
  generate_response  — все 4 категории / неизвестная / приветствие / подпись
"""

import pytest
from app.services.analyzer import TextAnalyzer


@pytest.fixture
def az():
    return TextAnalyzer()


# ═══════════════════════════════════════════
# analyze_tone
# ═══════════════════════════════════════════

class TestAnalyzeTone:
    def test_negative_single_keyword(self, az):
        assert az.analyze_tone("Прибор сломан") == "Негатив"

    def test_negative_multiple_keywords(self, az):
        assert az.analyze_tone("Срочно! Авария! Убытки!") == "Негатив"

    def test_positive_single_keyword(self, az):
        assert az.analyze_tone("Спасибо за помощь") == "Позитив"

    def test_positive_multiple_keywords(self, az):
        assert az.analyze_tone("Спасибо, отлично, благодарим!") == "Позитив"

    def test_neutral_no_keywords(self, az):
        assert az.analyze_tone("Прошу уточнить информацию о приборе.") == "Нейтраль"

    def test_neutral_equal_score(self, az):
        # ровно по одному слову из каждой группы → нейтраль
        assert az.analyze_tone("Спасибо, но есть проблем с прибором.") == "Нейтраль"

    def test_empty_string(self, az):
        assert az.analyze_tone("") == "Нейтраль"

    def test_case_insensitive_negative(self, az):
        assert az.analyze_tone("СРОЧНО НЕ ВКЛЮЧ прибор") == "Негатив"

    def test_case_insensitive_positive(self, az):
        assert az.analyze_tone("СПАСИБО ОТЛИЧНО") == "Позитив"

    def test_negative_wins_over_positive(self, az):
        # 3 негатив vs 1 позитив
        assert az.analyze_tone("не работает сломан авария спасибо") == "Негатив"

    def test_positive_wins_over_negative(self, az):
        # 3 позитив vs 1 негатив
        assert az.analyze_tone("спасибо благодар отлично ошибк") == "Позитив"


# ═══════════════════════════════════════════
# classify_category
# ═══════════════════════════════════════════

class TestClassifyCategory:
    def test_documentation_passport(self, az):
        assert az.classify_category("Прошу выслать паспорт прибора") == "Документация"

    def test_documentation_certificate(self, az):
        assert az.classify_category("Нужен сертификат соответствия") == "Документация"

    def test_documentation_document(self, az):
        assert az.classify_category("Предоставьте документ на оборудование") == "Документация"

    def test_documentation_instruction(self, az):
        assert az.classify_category("Пришлите инструкцию по эксплуатации") == "Документация"

    def test_calibration_keyword(self, az):
        assert az.classify_category("Требуется калибровка датчика") == "Калибровка"

    def test_calibration_poverka(self, az):
        assert az.classify_category("Проведите поверку оборудования") == "Калибровка"

    def test_calibration_nastrojka(self, az):
        assert az.classify_category("Требуется настройка прибора") == "Калибровка"

    def test_malfunction_ne_rabotaet(self, az):
        assert az.classify_category("Прибор не работает вторые сутки") == "Неисправность"

    def test_malfunction_ne_vklyuchaetsya(self, az):
        assert az.classify_category("Прибор не включается") == "Неисправность"

    def test_malfunction_sloman(self, az):
        assert az.classify_category("Датчик сломан") == "Неисправность"

    def test_malfunction_avariya(self, az):
        assert az.classify_category("Авария на линии") == "Неисправность"

    def test_malfunction_error(self, az):
        assert az.classify_category("Выдаёт ошибку E04") == "Неисправность"

    def test_general_default(self, az):
        assert az.classify_category("Хотел бы узнать о ценах и гарантии") == "Общий вопрос"

    def test_empty_string(self, az):
        assert az.classify_category("") == "Общий вопрос"

    def test_case_insensitive(self, az):
        assert az.classify_category("КАЛИБРОВКА ПРИБОРА") == "Калибровка"

    def test_first_matching_rule_wins(self, az):
        # "паспорт" (Документация) встречается раньше в правилах, чем "сломан"
        result = az.classify_category("нужен паспорт, прибор сломан")
        assert result == "Документация"


# ═══════════════════════════════════════════
# extract_devices
# ═══════════════════════════════════════════

class TestExtractDevices:
    def test_zav_nomer_keyword(self, az):
        result = az.extract_devices("заводской номер 12345")
        assert "12345" in result

    def test_zav_short_keyword(self, az):
        result = az.extract_devices("зав. номер 67890")
        assert "67890" in result

    def test_cyrillic_series(self, az):
        result = az.extract_devices("прибор НК-001")
        assert "НК-001" in result

    def test_hash_sign_pattern(self, az):
        result = az.extract_devices("заводской № А-2241")
        assert "А-2241" in result

    def test_multiple_devices_comma(self, az):
        result = az.extract_devices("заводские номера: НК-001, НК-002, НК-003")
        assert "НК-001" in result
        assert "НК-002" in result
        assert "НК-003" in result

    def test_no_devices_returns_empty(self, az):
        assert az.extract_devices("Добрый день, прошу помочь.") == ""

    def test_email_not_extracted_as_device(self, az):
        result = az.extract_devices("Пишите на support@enigma.ru")
        assert "@" not in result

    def test_five_digit_number(self, az):
        result = az.extract_devices("прибор 54321")
        assert "54321" in result

    def test_short_tokens_ignored(self, az):
        # токен длиной < 4 символов не должен попасть
        result = az.extract_devices("зав. № 123")
        assert result == "" or "123" not in result


# ═══════════════════════════════════════════
# extract_email
# ═══════════════════════════════════════════

class TestExtractEmail:
    def test_simple_email(self, az):
        assert az.extract_email("test@example.com") == "test@example.com"

    def test_email_with_dots_in_local(self, az):
        assert az.extract_email("ivan.petrov@company.ru") == "ivan.petrov@company.ru"

    def test_email_in_sentence(self, az):
        result = az.extract_email("Напишите на support@enigma.ru для уточнений.")
        assert result == "support@enigma.ru"

    def test_no_email_returns_empty(self, az):
        assert az.extract_email("Нет контактной информации") == ""

    def test_empty_string(self, az):
        assert az.extract_email("") == ""

    def test_first_email_extracted(self, az):
        # несколько email — берётся первый
        result = az.extract_email("a@a.ru и b@b.ru")
        assert result == "a@a.ru"


# ═══════════════════════════════════════════
# extract_phone
# ═══════════════════════════════════════════

class TestExtractPhone:
    def test_plus7_with_brackets(self, az):
        result = az.extract_phone("+7 (999) 123-45-67")
        assert "999" in result and "123" in result

    def test_8_prefix(self, az):
        result = az.extract_phone("8 (347) 200-10-20")
        assert result != ""

    def test_phone_in_sentence(self, az):
        result = az.extract_phone("Звоните: +7 (855) 555-00-11 в рабочее время.")
        assert "855" in result

    def test_no_phone_returns_empty(self, az):
        assert az.extract_phone("Нет телефона в тексте.") == ""

    def test_empty_string(self, az):
        assert az.extract_phone("") == ""


# ═══════════════════════════════════════════
# extract_name
# ═══════════════════════════════════════════

class TestExtractName:
    def test_regards_pattern_two_words(self, az):
        result = az.extract_name("С уважением, Иванов Иван")
        assert "Иванов" in result

    def test_regards_pattern_three_words(self, az):
        result = az.extract_name("С уважением, Смирнов Алексей Петрович")
        assert "Смирнов" in result and "Алексей" in result

    def test_menya_zovut_pattern(self, az):
        result = az.extract_name("Меня зовут Петрова Светлана")
        assert "Петрова" in result

    def test_no_name_returns_empty(self, az):
        assert az.extract_name("Добрый день, прошу помочь с прибором.") == ""

    def test_empty_string(self, az):
        assert az.extract_name("") == ""

    def test_case_insensitive_trigger(self, az):
        result = az.extract_name("с уважением, Козлов Денис")
        assert "Козлов" in result


# ═══════════════════════════════════════════
# summarize
# ═══════════════════════════════════════════

class TestSummarize:
    def test_short_text_unchanged(self, az):
        assert az.summarize("Прибор не работает") == "Прибор не работает"

    def test_first_sentence_only(self, az):
        result = az.summarize("Первое предложение. Второе предложение.")
        assert "Первое" in result
        assert "Второе" not in result

    def test_long_text_truncated(self, az):
        long_text = "А" * 110
        result = az.summarize(long_text)
        assert result.endswith("...")
        assert len(result) == 100  # 97 + "..."

    def test_exactly_100_chars_not_truncated(self, az):
        text = "Б" * 100
        result = az.summarize(text)
        assert not result.endswith("...")
        assert len(result) == 100

    def test_101_chars_truncated(self, az):
        text = "В" * 101
        result = az.summarize(text)
        assert result.endswith("...")

    def test_empty_string(self, az):
        assert az.summarize("") == ""


# ═══════════════════════════════════════════
# generate_response
# ═══════════════════════════════════════════

class TestGenerateResponse:
    def test_malfunction_contains_instructions(self, az):
        result = az.generate_response("Неисправность")
        assert "Отключите прибор" in result

    def test_calibration_mentions_period(self, az):
        result = az.generate_response("Калибровка")
        assert "6 месяцев" in result

    def test_documentation_mentions_delivery(self, az):
        result = az.generate_response("Документация")
        assert "1 рабочего дня" in result

    def test_general_question_response(self, az):
        result = az.generate_response("Общий вопрос")
        assert "обработан" in result.lower()

    def test_unknown_category_uses_fallback(self, az):
        result = az.generate_response("НепонятнаяКатегория")
        assert "обработан" in result.lower()

    def test_all_responses_start_with_greeting(self, az):
        for cat in ["Неисправность", "Калибровка", "Документация", "Общий вопрос"]:
            assert az.generate_response(cat).startswith("Уважаемый(-ая) клиент!")

    def test_all_responses_end_with_signature(self, az):
        for cat in ["Неисправность", "Калибровка", "Документация", "Общий вопрос"]:
            assert "технической поддержки ЭРИС" in az.generate_response(cat)
