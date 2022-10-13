from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Extra, Field
from tabulate import tabulate


class DocsField(BaseModel):

    name: str
    value: Optional[str] = None
    tooltip: Optional[str] = None


class Capability(Enum):
    properties = "properties"
    catalog = "catalog"
    discover = "discover"
    state = "state"
    about = "about"
    stream_maps = "stream-maps"
    activate_version = "activate-version"
    batch = "batch"
    test = "test"
    log_based = "log-based"
    schema_flattening = "schema-flattening"


class Kind(Enum):
    oauth = "oauth"
    hidden = "hidden"
    password = "password"
    date_iso8601 = "date_iso8601"
    file = "file"
    email = "email"
    integer = "integer"
    options = "options"
    object = "object"
    array = "array"
    boolean = "boolean"
    string = "string"


class Oauth(BaseModel):
    provider: str = Field(
        ...,
        description="The name of a Meltano-supported OAuth provider",
        examples=["google-adwords"],
    )


class Setting(BaseModel):
    class Config:
        extra = Extra.forbid
        use_enum_values = True

    name: str = Field(
        ..., description="The name of the setting", examples=["account_id"]
    )
    aliases: Optional[List[str]] = Field(
        None,
        description="Alternative setting names that can be used in 'meltano.yml' and 'meltano config set'",
        examples=["accountId", "account_identifier"],
    )
    label: Optional[str] = Field(
        None,
        description="A user friendly label for the setting",
        examples=["Account ID"],
    )
    value: Optional[Any] = Field(
        None, description="The default value of this setting if not otherwise defined"
    )
    placeholder: Optional[str] = Field(
        None, description="A placeholder value for this setting", examples=["Ex. 18161"]
    )
    kind: Optional[Kind] = Field(
        None, description="The type of value this setting contains"
    )
    description: Optional[str] = Field(
        None,
        description="A description for what this setting does",
        examples=["The unique account identifier for your Stripe Account"],
    )
    tooltip: Optional[str] = Field(
        None,
        description="A phrase to provide additional information on this setting",
        examples=["Here is some additional info..."],
    )
    documentation: Optional[str] = Field(
        None,
        description="A link to documentation on this setting",
        examples=["https://meltano.com/"],
    )
    protected: Optional[bool] = Field(
        False, description="A protected setting cannot be changed from the UI"
    )
    env: Optional[str] = Field(
        None,
        description="An alternative environment variable name to populate with this settings value in the plugin environment.",
        examples=["GITLAB_API_TOKEN", "FACEBOOK_ADS_ACCESS_TOKEN"],
    )
    value_processor: Optional[Any] = Field(
        None, description="Use with `kind: object` to automatically nest flattened keys"
    )
    oauth: Optional[Oauth] = None


class SettingStore(Enum):
    CONFIG_OVERRIDE = "config_override"
    ENV = "env"
    DOTENV = "dotenv"
    MELTANO_ENV = "meltano_environment"
    MELTANO_YML = "meltano_yml"
    DB = "db"
    INHERITED = "inherited"
    DEFAULT = "default"
    AUTO = "auto"


class SettingValue(BaseModel):
    name: str
    is_redacted: bool
    source: SettingStore
    value: Optional[Any] = None

    class Config:
        use_enum_values = True


class EnvironmentSettingValues(BaseModel):

    setting_values: List[SettingValue]
    environment: Optional[str] = "base"

    def as_table(self):
        headers = [":octicon:`lock`", "Setting", "Value", "Source"]
        rows = [
            [
                ":octicon:`lock`" if setting.is_redacted else "",
                f"``{setting.name}``",
                setting.value or "",
                setting.source,
            ]
            for setting in self.setting_values
        ]
        return tabulate(rows, headers=headers, tablefmt="rst")


class ExtractorDocs(BaseModel):
    """Extractor details, used when rendering docs."""

    name: str
    label: Optional[str] = None
    variant: Optional[str] = None
    description: Optional[DocsField] = None
    capabilities: Optional[List[Capability]] = []
    settings: Optional[List[Setting]] = []
    environment_setting_values: Optional[List[EnvironmentSettingValues]] = []

    class Config:
        use_enum_values = True
