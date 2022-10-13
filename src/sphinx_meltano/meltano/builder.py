import json
import shutil
from pathlib import Path
from typing import List

import commonmark
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from meltano.core.db import project_engine
from meltano.core.environment_service import EnvironmentService
from meltano.core.plugin import PluginType
from meltano.core.plugin.settings_service import PluginSettingsService
from meltano.core.plugin_discovery_service import PluginDiscoveryService
from meltano.core.project import Project
from meltano.core.project_plugins_service import DefinitionSource, ProjectPluginsService
from meltano.core.settings_store import SettingValueStore
from tabulate import tabulate

from ..settings import TEMPLATE_DIR
from .details import (
    DocsField,
    EnvironmentSettingValues,
    ExtractorDocs,
    Setting,
    SettingStore,
    SettingValue,
)


class BaseDocsBuilder:
    def __init__(
        self,
        project_root: Path,
        docs_root: Path,
        template_dir: Path,
        include_setting_values: bool = False,
    ):
        self.project_root = project_root
        self.docs_root = Path(docs_root)
        self.include_setting_values = include_setting_values

        self.project = Project(root=self.project_root)
        self.project_plugins_service = ProjectPluginsService(project=self.project)

        _, Session = project_engine(self.project)  # noqa: N806
        self.session = Session()

        template_paths = [TEMPLATE_DIR]

        if template_dir:
            # Put at the front so it's loaded first
            template_paths.insert(0, template_dir)

        self.jinja_env = Environment(
            loader=FileSystemLoader(template_paths),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        if self.docs_root.exists():
            # clean up previous run
            shutil.rmtree(self.docs_root)
        self.docs_root.mkdir(parents=True, exist_ok=True)


class ProjectDocsBuilder(BaseDocsBuilder):
    """Render docs for a Meltano Project."""

    def _get_environment_setting_values(self, plugin, environment="base"):
        if environment == "base":
            self.project.deactivate_environment()
        else:
            self.project.activate_environment(environment)

        plugin_settings_service = PluginSettingsService(
            project=self.project,
            plugin=plugin,
            plugins_service=self.project_plugins_service,
        )
        config = plugin_settings_service.config_with_metadata(
            session=self.session, extras=False, redacted=True
        )
        setting_values = []
        for setting in config.values():
            if environment == "base" and setting["source"] in {
                SettingValueStore.DEFAULT,
                SettingValueStore.MELTANO_YML,
                SettingValueStore.INHERITED,
                SettingValueStore.DOTENV,
            }:
                setting_values.append(
                    SettingValue(
                        name=setting["name"],
                        value=setting["value"],
                        is_redacted=setting["setting"].is_redacted,
                        source=SettingStore(setting["source"]),
                    )
                )
            elif setting["source"] in {SettingValueStore.MELTANO_ENV}:
                setting_values.append(
                    SettingValue(
                        name=setting["name"],
                        value=setting["value"],
                        is_redacted=setting["setting"].is_redacted,
                        source=SettingStore(setting["source"]),
                    )
                )
        return EnvironmentSettingValues(
            environment=environment, setting_values=setting_values
        )

    def get_all_settings(self, plugin):
        environments = EnvironmentService(project=self.project).list_environments()
        base = self._get_environment_setting_values(plugin, "base")
        environment_settings = [
            self._get_environment_setting_values(plugin, environment.name)
            for environment in environments
        ]
        return [base] + environment_settings

    def get_extractor_documentation(self, plugin) -> dict:
        """Very basic plugin definition information.

        TODO: Replace with something that hits the Hub API.
        """
        with self.project_plugins_service.use_preferred_source(DefinitionSource.HUB):
            hub_plugin, _ = self.project_plugins_service.find_parent(plugin)

        description = (
            DocsField(name="description", value=plugin.description)
            if plugin.description
            else DocsField(
                name="description",
                value=hub_plugin.description,
                tooltip=f"This value was retrieved from Meltano Hub. Use 'meltano config {plugin.name} set description <value>' to override.",
            )
        )
        settings = [Setting.parse_obj(setting) for setting in plugin.all_settings]
        current_settings = []
        capabilities = plugin.capabilities
        if self.include_setting_values:
            current_settings = self.get_all_settings(plugin=plugin)

        return ExtractorDocs(
            name=plugin.name,
            label=plugin.label,
            variant=plugin.variant,
            description=description,
            capabilities=capabilities,
            settings=settings,
            environment_setting_values=current_settings,
        )

    def render_extractors(self, extractors):
        """Write plugin details into valid .rst files in the docs source."""
        # get extractor details
        extractor_definitions = [
            self.get_extractor_documentation(plugin) for plugin in extractors
        ]
        # write extractor details to JSON
        extract_root = self.docs_root / "extract"
        extract_root.mkdir(parents=True, exist_ok=True)
        extractor_def_files = []
        for plugin_def in extractor_definitions:
            plugin_def_file_path = (
                extract_root / f"{plugin_def.name}-{plugin_def.variant}.json"
            )
            with open(plugin_def_file_path, "w") as plugin_def_file:
                json.dump(plugin_def.dict(), plugin_def_file)
            extractor_def_files.append(str(plugin_def_file_path))
        # render extractor directives
        extractor_directives = []
        for extractor_def, extractor_def_file in zip(
            extractor_definitions, extractor_def_files
        ):
            rst = self.jinja_env.get_template("build/extractor.rst").render(
                extractor_def=extractor_def_file
            )
            with open(
                extract_root / f"{extractor_def.name}-{extractor_def.variant}.rst",
                "wb+",
            ) as extractor_docs:
                extractor_docs.write(rst.encode("utf-8"))
            extractor_directives.append(
                f"extract/{extractor_def.name}-{extractor_def.variant}"
            )
        # write extractors toc
        rst = self.jinja_env.get_template("build/extractors.rst").render(
            include=extractor_directives
        )
        with open(
            self.docs_root / "extractors.rst",
            "wb+",
        ) as extractors_docs:
            extractors_docs.write(rst.encode("utf-8"))

    def render_plugins(self, include: List[str]):
        rst = self.jinja_env.get_template("build/plugins.rst").render(include=include)
        with open(self.docs_root / "plugins.rst", "wb+") as plugin_docs:
            plugin_docs.write(rst.encode("utf-8"))

    def render_index(self, include: List[str]):
        rst = self.jinja_env.get_template("build/index.rst").render(include=include)
        with open(self.docs_root / "index.rst", "wb+") as index:
            index.write(rst.encode("utf-8"))

    def render(self):
        extractors = self.project_plugins_service.get_plugins_of_type(
            plugin_type=PluginType.EXTRACTORS, ensure_parent=True
        )
        self.render_extractors(extractors)
        self.render_plugins(include=["extractors"])
        self.render_index(include=["plugins"])
