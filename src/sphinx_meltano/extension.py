import os

from .directives import MeltanoExtractorDirective
from .meltano.builder import ProjectDocsBuilder


def run_meltano_autodoc(app):
    """Generate .rst files on the fly from a meltano project."""
    normalized_docs_root = os.path.normpath(
        os.path.join(app.srcdir, app.config.meltano_docs_root)
    )
    renderer = ProjectDocsBuilder(
        project_root=app.config.meltano_project_root,
        docs_root=normalized_docs_root,
        template_dir=app.config.meltano_template_dir,
        include_setting_values=app.config.meltano_include_setting_values,
    )
    renderer.render()


def setup(app):
    app.connect("builder-inited", run_meltano_autodoc)
    app.add_config_value("meltano_project_root", "meltano", "html")
    app.add_config_value("meltano_docs_root", "meltano", "html")
    app.add_config_value("meltano_template_dir", None, "html")
    app.add_config_value("meltano_include_setting_values", False, "html")
    app.add_directive("meltano-extractor", MeltanoExtractorDirective)
    return {
        "version": "0.1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
        "needs_extensions": {"sphinx_design": ">=0.3.0"},
    }
