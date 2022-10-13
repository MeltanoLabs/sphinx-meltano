import json
from pathlib import Path

import commonmark
from docutils.frontend import OptionParser
from docutils.utils import new_document
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from sphinx.parsers import RSTParser
from sphinx.util.docutils import SphinxDirective
from tabulate import tabulate

from .meltano.details import ExtractorDocs
from .settings import TEMPLATE_DIR


class MeltanoPluginDirective(SphinxDirective):
    """Base plugin directive."""

    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = True

    @staticmethod
    def convert_md_to_rst(md):
        if md:
            ast = commonmark.Parser().parse(md)
            return commonmark.ReStructuredTextRenderer().render(ast).rstrip()
        return ""

    @staticmethod
    def convert_md_to_html(md):
        if md:
            ast = commonmark.Parser().parse(md)
            return commonmark.HtmlRenderer().render(ast).rstrip()
        return ""

    def parse_rst(self, text):
        """Parse rst into a toctree.

        Kudos to https://sammart.in/post/2021-05-10-external-data-sphinx-extension/
        for this idea.
        """
        parser = RSTParser()
        parser.set_application(self.env.app)
        settings = OptionParser(
            defaults=self.env.settings,
            components=(RSTParser,),
            read_config_files=True,
        ).get_default_values()
        document = new_document("<rst-doc>", settings=settings)
        parser.parse(text, document)
        return document.children

    def render_template(self, template_name, docs):
        """Render jinja template with passed kwargs."""
        template_paths = [TEMPLATE_DIR]
        if self.config.meltano_template_dir:
            # Put at the front so it's loaded first
            template_paths.insert(0, self.app.config.meltano_template_dir)

        jinja_env = Environment(
            loader=FileSystemLoader(template_paths),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        jinja_env.globals.update(md2rst=self.convert_md_to_rst)
        jinja_env.globals.update(md2html=self.convert_md_to_html)

        return jinja_env.get_template(template_name).render(docs=docs)

    def get_plugin_definition(self):
        # check path exists
        fpth = Path(self.arguments[0])
        if not fpth.exists():
            raise self.error(
                'Argument file path "%s" does not exist.' % self.arguments[0]
            )
        # check path refers to a file
        if not fpth.is_file():
            raise self.error(
                'Argument file path "%s" is not a file.' % self.arguments[0]
            )
        return ExtractorDocs.parse_file(fpth)


class MeltanoExtractorDirective(MeltanoPluginDirective):
    def run(self) -> list:
        # check if directive recieved valid json path or json
        plugin_definition = self.get_plugin_definition()
        rst = self.render_template("plugin.rst", plugin_definition)
        return self.parse_rst(rst)
