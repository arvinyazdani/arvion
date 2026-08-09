from django.core.management.base import BaseCommand, CommandError

from assessments.management.commands.seed_assessment_banks import validate_bank
from assessments.quality import audit_bank
from assessments.question_banks.english import QUESTIONS as ENGLISH, SECTIONS as ENGLISH_SECTIONS
from assessments.question_banks.python_django import QUESTIONS as PYTHON, SECTIONS as PYTHON_SECTIONS


class Command(BaseCommand):
    help = "Audit source question banks for structural and editorial quality risks"

    def add_arguments(self, parser):
        parser.add_argument("--strict-editorial", action="store_true")

    def handle(self, *args, **options):
        total_warnings = 0
        for name, questions, sections in (
            ("english", ENGLISH, ENGLISH_SECTIONS),
            ("python-django", PYTHON, PYTHON_SECTIONS),
        ):
            validate_bank(questions, sections)
            report = audit_bank(questions, sections)
            if report["issues"]:
                raise CommandError(f"{name}: " + "; ".join(report["issues"]))
            total_warnings += len(report["warnings"])
            self.stdout.write(
                f"{name}: {report['question_count']} questions; "
                f"{report['subskill_count']} subskills; {len(report['warnings'])} editorial warnings"
            )
            for warning in report["warnings"]:
                self.stdout.write(self.style.WARNING(f"  {warning}"))
        if options["strict_editorial"] and total_warnings:
            raise CommandError(f"Question banks have {total_warnings} unresolved editorial warnings")
        self.stdout.write(self.style.SUCCESS("Question-bank structural audit passed."))
