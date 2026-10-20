"""Central indexability policy for public demo previews."""

FEATURED_DEMO_SLUGS = (
    "ahanino-b2b-marketplace",
    "raya-personal-finance",
    "kimia-medical-crm",
)


def is_featured_demo(slug):
    return slug in FEATURED_DEMO_SLUGS
