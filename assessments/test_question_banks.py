from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management.base import CommandError
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from .management.commands.seed_assessment_banks import validate_bank
from .question_banks.english import BANK_VERSION as ENGLISH_BANK_VERSION, QUESTIONS, SECTIONS
from .question_banks.python_django import BANK_VERSION as PYTHON_BANK_VERSION, QUESTIONS as PYTHON_QUESTIONS, SECTIONS as PYTHON_SECTIONS
from .templatetags.assessment_extras import inline_code
from .models import Exam, ExamEntitlement, ExamVersion, Order
from .integrity import expected_seconds
from .services import _level_for, start_attempt
from .quality import audit_bank


class EnglishQuestionBankTests(SimpleTestCase):
    def test_bank_has_exactly_two_hundred_valid_questions(self):
        self.assertEqual(len(QUESTIONS), 200)
        validate_bank(QUESTIONS, SECTIONS)

    def test_final_blueprint_selects_fifty_questions(self):
        self.assertEqual(sum(section[4] for section in SECTIONS), 50)
        distribution = Counter()
        for section in SECTIONS:
            distribution.update({int(level): count for level, count in section[5].items()})
        self.assertEqual(distribution, {2: 2, 3: 8, 4: 20, 5: 20})

    def test_every_v5_selectable_question_is_curated_for_teacher_screening(self):
        selectable = []
        for section in SECTIONS:
            allowed_levels = {int(level) for level in section[5]}
            selectable.extend(
                question for question in QUESTIONS
                if question["section"] == section[0] and question["difficulty"] in allowed_levels
            )

        self.assertTrue(selectable)
        self.assertTrue(all(question.get("teacher_v5_curated") is True for question in selectable))
        prompts = {question["prompt"] for question in selectable}
        self.assertNotIn("He asked me where I ___ the file.", prompts)
        self.assertNotIn("She ___ coffee every morning.", prompts)
        self.assertTrue(all(question["difficulty"] >= 2 for question in selectable))

    def test_v5_selectable_choices_do_not_reveal_the_key_by_length(self):
        by_section = {}
        for question in QUESTIONS:
            if question["difficulty"] not in {2, 3, 4, 5}:
                continue
            lengths = [len(choice.split()) for choice in question["choices"]]
            by_section.setdefault(question["section"], []).append(lengths[0] > max(lengths[1:]))

        all_flags = [flag for flags in by_section.values() for flag in flags]
        self.assertLessEqual(sum(all_flags) / len(all_flags), .25)
        for section, flags in by_section.items():
            with self.subTest(section=section):
                self.assertLessEqual(sum(flags) / len(flags), .35)

    def test_v5_pedagogy_distractors_are_plausible_and_professional(self):
        selectable_choices = [
            choice.casefold()
            for question in QUESTIONS if question["difficulty"] in {2, 3, 4, 5}
            for choice in question["choices"]
        ]
        childish_markers = (
            "larger font", "ban indirect requests", "rewrite everything",
            "never make claims", "spelling of ‘window’", "no relationship to common cases",
        )
        for marker in childish_markers:
            self.assertFalse(any(marker in choice for choice in selectable_choices), marker)

        stance_item = next(
            question for question in QUESTIONS
            if question["prompt"].startswith("A C1 learner repeatedly writes")
        )
        self.assertTrue(all(len(choice.split()) >= 9 for choice in stance_item["choices"]))
        validity_item = next(
            question for question in QUESTIONS
            if question["prompt"].startswith("A test labels a candidate C2")
        )
        self.assertIn("productive, interactive", validity_item["choices"][0])

    def test_writing_objective_has_twenty_curated_items(self):
        writing = [question for question in QUESTIONS if question["section"] == "writing-objective"]
        self.assertEqual(len(writing), 20)
        self.assertTrue(all(question["question_type"] == "writing_objective" for question in writing))
        selectable = [question for question in writing if question["difficulty"] in {4, 5}]
        self.assertTrue(all(question.get("teacher_v5_curated") is True for question in selectable))
        self.assertTrue(all(question["suggested_seconds"] == 70 for question in selectable))

    def test_listening_has_thirty_two_items_and_real_audio_assets(self):
        listening = [question for question in QUESTIONS if question["section"] == "listening"]
        self.assertEqual(len(listening), 32)
        self.assertEqual(len({question["audio_path"] for question in listening}), 12)
        for question in listening:
            self.assertEqual(question["question_type"], "listening")
            self.assertEqual(question["max_plays"], 2)
            self.assertTrue(question["transcript"])
            audio_file = Path(settings.BASE_DIR) / "core" / "static" / question["audio_path"]
            self.assertTrue(audio_file.exists())
            self.assertGreater(audio_file.stat().st_size, 10_000)

    def test_every_question_has_one_answer_key_and_explanation(self):
        for question in QUESTIONS:
            self.assertEqual(len(question["choices"]), 4)
            self.assertTrue(question["choices"][0])
            self.assertTrue(question["explanation"])

    def test_validator_rejects_duplicate_choices(self):
        invalid = [{"section": "only", "choices": ("a", "a", "b", "c"), "difficulty": 1}]
        with self.assertRaises(CommandError):
            validate_bank(invalid, (("only", "بخش", "Section", 1),))

    def test_validator_rejects_an_impossible_explicit_blueprint(self):
        invalid = [{
            "section": "only", "prompt": "A complete prompt", "choices": ("a", "b", "c", "d"),
            "difficulty": 3, "explanation": "A specific explanation",
        }]
        with self.assertRaisesMessage(CommandError, "does not have 1 questions at difficulty 5"):
            validate_bank(invalid, (("only", "بخش", "Section", 1, 1, {"5": 1}),))


class PythonQuestionBankTests(SimpleTestCase):
    def test_bank_has_exactly_two_hundred_valid_questions(self):
        self.assertEqual(len(PYTHON_QUESTIONS), 200)
        validate_bank(PYTHON_QUESTIONS, PYTHON_SECTIONS)

    def test_exam_blueprint_selects_fifty_questions_from_seven_sections(self):
        self.assertEqual(len(PYTHON_SECTIONS), 7)
        self.assertEqual(sum(section[4] for section in PYTHON_SECTIONS), 50)

    def test_every_question_has_complete_explanations_and_unique_prompts(self):
        prompts_fa = [question["prompt_fa"].strip().casefold() for question in PYTHON_QUESTIONS]
        prompts_en = [question["prompt_en"].strip().casefold() for question in PYTHON_QUESTIONS]
        self.assertEqual(len(set(prompts_fa)), 200)
        self.assertEqual(len(set(prompts_en)), 200)
        for question in PYTHON_QUESTIONS:
            self.assertTrue(question["explanation_fa"])
            self.assertTrue(question["explanation_en"])
            self.assertEqual(len(question["choice_explanations_fa"]), 4)
            self.assertEqual(len(question["choice_explanations_en"]), 4)

    def test_every_prompt_is_bilingual(self):
        for question in PYTHON_QUESTIONS:
            self.assertTrue(question["prompt_fa"])
            self.assertTrue(question["prompt_en"])
            self.assertNotEqual(question["prompt_fa"], question["prompt_en"])

    def test_inline_code_keeps_ascii_and_escapes_question_html(self):
        rendered = str(inline_code('مقدار `<x 1>` <script>bad</script>'))
        self.assertIn('data-ascii', rendered)
        self.assertIn('&lt;x 1&gt;', rendered)
        self.assertNotIn('<script>', rendered)


class QuestionBankEditorialAuditTests(SimpleTestCase):
    def test_audit_reports_normalized_choice_collisions(self):
        questions = [{
            "prompt": "A sufficiently long prompt for comparison?",
            "section": "grammar", "difficulty": 2,
            "choices": ("Yes", " yes ", "No", "Maybe"),
            "explanation": "Specific rationale.",
        }]
        report = audit_bank(questions, (("grammar", "گرامر", "Grammar", 1, 1),))
        self.assertTrue(any("choices collide" in issue for issue in report["issues"]))

    def test_current_banks_have_no_structural_audit_issues(self):
        for questions, sections in (
            (QUESTIONS, SECTIONS), (PYTHON_QUESTIONS, PYTHON_SECTIONS),
        ):
            report = audit_bank(questions, sections)
            self.assertEqual(report["issues"], [])
            self.assertGreaterEqual(report["subskill_count"], 20)

    def test_current_banks_have_no_automated_editorial_warnings(self):
        for questions, sections in (
            (QUESTIONS, SECTIONS), (PYTHON_QUESTIONS, PYTHON_SECTIONS),
        ):
            self.assertEqual(audit_bank(questions, sections)["warnings"], [])


class BenchmarkCommandTests(TestCase):
    def test_benchmark_rolls_back_all_synthetic_data(self):
        call_command("benchmark_assessment_engine", attempts=2, verbosity=0)
        self.assertFalse(Exam.objects.filter(slug="benchmark-50").exists())
        self.assertFalse(get_user_model().objects.filter(email="benchmark@local.invalid").exists())


class PublishedPythonBankTests(TestCase):
    def test_seed_command_bootstraps_empty_database_and_is_idempotent(self):
        call_command("seed_assessment_banks", verbosity=0)
        call_command("seed_assessment_banks", verbosity=0)

        self.assertEqual(Exam.objects.count(), 2)
        english = Exam.objects.get(slug="english-placement-a1-c1")
        python = Exam.objects.get(slug="python-django-professional")
        self.assertEqual(english.price_irr, 2_000_000)
        self.assertEqual(english.versions.get(version=ENGLISH_BANK_VERSION).questions.count(), 200)
        self.assertEqual(python.versions.get(version=PYTHON_BANK_VERSION).questions.count(), 200)
        self.assertEqual(english.versions.filter(version=ENGLISH_BANK_VERSION).count(), 1)
        self.assertEqual(python.versions.filter(version=PYTHON_BANK_VERSION).count(), 1)

    def test_current_versions_publish_and_build_a_balanced_fifty_question_attempt(self):
        english_exam = Exam.objects.create(
            slug="english-placement-a1-c1", title_fa="انگلیسی", title_en="English",
            description_fa="توضیح", description_en="Description", language_mode="en",
            question_count=50,
        )
        python_exam = Exam.objects.create(
            slug="python-django-professional", title_fa="پایتون", title_en="Python",
            description_fa="توضیح", description_en="Description", language_mode="bilingual",
            question_count=50,
        )
        call_command("seed_assessment_banks", verbosity=0)
        english_exam.refresh_from_db()
        english_version = ExamVersion.objects.get(exam=english_exam, version=ENGLISH_BANK_VERSION, is_published=True)
        self.assertEqual(english_exam.duration_minutes, 75)
        self.assertEqual(english_version.questions.count(), 200)
        self.assertEqual(english_version.sections.get(code="writing-objective").question_count, 5)
        self.assertEqual(english_version.sections.get(code="listening").question_count, 8)
        version = ExamVersion.objects.get(exam=python_exam, version=PYTHON_BANK_VERSION, is_published=True)
        self.assertEqual(version.questions.count(), 200)
        self.assertEqual(sum(section.question_count for section in version.sections.all()), 50)
        user = get_user_model().objects.create_user(
            username="bank-test@example.com", email="bank-test@example.com", password="test",
        )
        order = Order.objects.create(user=user, exam=python_exam, amount_irr=500_000, status="paid")
        entitlement = ExamEntitlement.objects.create(
            user=user, exam=python_exam, order=order, attempts_remaining=1,
        )
        attempt, _ = start_attempt(entitlement.pk, user)
        self.assertEqual(attempt.version, version)
        self.assertEqual(attempt.attempt_questions.count(), 50)
        for section in version.sections.all():
            rows = attempt.attempt_questions.filter(question__section=section)
            self.assertEqual(rows.count(), section.question_count)
            actual = {}
            for difficulty in rows.values_list("question__difficulty", flat=True):
                actual[str(difficulty)] = actual.get(str(difficulty), 0) + 1
            self.assertEqual(actual, section.difficulty_distribution)

    def test_english_teacher_attempt_uses_the_high_selectivity_blueprint(self):
        call_command("seed_assessment_banks", verbosity=0)
        exam = Exam.objects.get(slug="english-placement-a1-c1")
        user = get_user_model().objects.create_user(
            username="teacher-bank-test@example.com",
            email="teacher-bank-test@example.com",
            password="test",
        )
        order = Order.objects.create(user=user, exam=exam, amount_irr=2_000_000, status="paid")
        entitlement = ExamEntitlement.objects.create(
            user=user, exam=exam, order=order, attempts_remaining=1,
        )

        attempt, created = start_attempt(entitlement.pk, user)

        self.assertTrue(created)
        self.assertEqual(attempt.version.version, ENGLISH_BANK_VERSION)
        self.assertEqual(
            Counter(attempt.attempt_questions.values_list("question__difficulty", flat=True)),
            {2: 2, 3: 8, 4: 20, 5: 20},
        )
        authored_seconds = sum(
            expected_seconds(row.question.suggested_seconds, row.question.difficulty)
            for row in attempt.attempt_questions.select_related("question")
        )
        sampled_totals = [authored_seconds]
        sampled_question_sets = [{
            *attempt.attempt_questions.values_list("question_id", flat=True),
        }]
        for index in range(4):
            sample_user = get_user_model().objects.create_user(
                username=f"teacher-bank-sample-{index}@example.com",
                email=f"teacher-bank-sample-{index}@example.com",
                password="test",
            )
            sample_order = Order.objects.create(
                user=sample_user, exam=exam, amount_irr=2_000_000, status="paid",
            )
            sample_entitlement = ExamEntitlement.objects.create(
                user=sample_user, exam=exam, order=sample_order, attempts_remaining=1,
            )
            sample_attempt, _ = start_attempt(sample_entitlement.pk, sample_user)
            sampled_totals.append(sum(
                expected_seconds(row.question.suggested_seconds, row.question.difficulty)
                for row in sample_attempt.attempt_questions.select_related("question")
            ))
            sampled_question_sets.append({
                *sample_attempt.attempt_questions.values_list("question_id", flat=True),
            })

        self.assertTrue(all(70 * 60 <= total <= 80 * 60 for total in sampled_totals))
        self.assertGreater(len({frozenset(question_ids) for question_ids in sampled_question_sets}), 1)

    def test_teacher_level_bands_apply_only_to_version_five_and_later(self):
        exam = Exam.objects.create(
            slug="english-placement-a1-c1", title_fa="انگلیسی", title_en="English",
            description_fa="توضیح", description_en="Description", language_mode="en",
            question_count=50,
        )

        self.assertEqual(_level_for(exam, 50, version_number=4)[0], "B1")
        self.assertEqual(_level_for(exam, 50, version_number=5)[0], "below-benchmark")
        self.assertEqual(_level_for(exam, 90, version_number=4)[0], "C1")
        self.assertEqual(_level_for(exam, 90, version_number=5)[0], "C1+")
        self.assertEqual(_level_for(exam, 97, version_number=5)[0], "exceptional-objective")
