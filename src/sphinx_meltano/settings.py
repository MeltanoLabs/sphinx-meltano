"""
Basic settings for Meltano projects.

You shouldn't need to touch this.
"""

import os

SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = os.path.join(SITE_ROOT, "templates")

DOCS_ROOT = "autoapi"
