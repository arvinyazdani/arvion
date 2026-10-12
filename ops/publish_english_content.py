"""Run with manage.py shell and owner approval; scoped, backed-up content release.

RVION_ENGLISH_RELEASE_DIRECTORY contains english_editions.py + english_content/.
Dry-run is default. Apply requires RVION_ENGLISH_APPLY=1 and a fresh absolute
RVION_ENGLISH_BACKUP_DIRECTORY. No source checkout, flags, migrations or other
records are changed. Restore only ENGLISH_FIELDS from before.json to roll back.
"""
import importlib.util
import json
import os
from pathlib import Path

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction

from blog.models import Post


release = Path(os.environ["RVION_ENGLISH_RELEASE_DIRECTORY"]).resolve(strict=True)
spec = importlib.util.spec_from_file_location("rvion_approved_english", release / "english_editions.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
apply = os.environ.get("RVION_ENGLISH_APPLY") == "1"
editions = module.load_english_editions()
slugs = [item["slug_fa"] for item in editions]


def snapshot():
    rows = list(Post.objects.filter(slug_fa__in=slugs).order_by("pk").values())
    for row in rows:
        row["tag_ids"] = list(Post.objects.get(pk=row["id"]).tags.order_by("pk").values_list("pk", flat=True))
    return rows


with transaction.atomic():
    if apply:
        list(Post.objects.select_for_update().filter(slug_fa__in=slugs).order_by("pk"))
    print("Preflight:", module.publish_english_editions())
    before = snapshot()
    if apply:
        backup = Path(os.environ["RVION_ENGLISH_BACKUP_DIRECTORY"])
        if not backup.is_absolute():
            raise ValueError("Backup path must be absolute")
        backup.mkdir(mode=0o700, parents=False, exist_ok=False)
        before_file = backup / "before.json"
        before_file.write_text(json.dumps(before, cls=DjangoJSONEncoder, ensure_ascii=False, indent=2), encoding="utf-8")
        before_file.chmod(0o600)
        if json.loads(before_file.read_text()) != json.loads(json.dumps(before, cls=DjangoJSONEncoder)):
            raise ValueError("Backup read-back failed")
        print("Result:", module.publish_english_editions(apply=True))
        after = snapshot()
        preserved = lambda rows: [{key: value for key, value in row.items()
                                   if key not in module.ENGLISH_FIELDS} for row in rows]
        if preserved(before) != preserved(after):
            raise ValueError("Non-English fields changed; rolling back")
        print("Verification:", module.publish_english_editions(), "Non-English fields unchanged.")
        print("Backup:", backup)
    else:
        print("Dry-run only; no database or backup writes.")
