"""Shared accessibility attributes for server-rendered Django forms."""


def enhance_form_accessibility(form, *, autocomplete=None):
    """Connect help/errors to controls and declare common input purposes."""

    autocomplete = autocomplete or {}
    bound_errors = form.errors if form.is_bound else {}
    for name, field in form.fields.items():
        bound_field = form[name]
        control_id = bound_field.auto_id
        described_by = []
        if field.help_text:
            described_by.append(f"{control_id}-help")
        if name in bound_errors:
            described_by.append(f"{control_id}-errors")
            field.widget.attrs["aria-invalid"] = "true"
        else:
            field.widget.attrs.pop("aria-invalid", None)
        if described_by:
            field.widget.attrs["aria-describedby"] = " ".join(described_by)
        else:
            field.widget.attrs.pop("aria-describedby", None)
        if name in autocomplete:
            field.widget.attrs["autocomplete"] = autocomplete[name]
