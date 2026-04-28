from enum import Enum
from typing import Literal, Union, cast

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import TypeAliasType


JsonValue = TypeAliasType(
    "JsonValue",
    Union[
        str,
        int,
        float,
        bool,
        None,
        list["JsonValue"],
        dict[str, "JsonValue"],
    ],
)
StructuredData = dict[str, JsonValue]

ToolName = Literal["echo", "disk_info", "system_info"]
KNOWN_TOOL_NAMES: tuple[ToolName, ...] = ("echo", "disk_info", "system_info")


class StrictArtifactModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class ToolPrecondition(str, Enum):
    AUTHENTICATED_CONTEXT = "authenticated_context"
    TOOL_REGISTERED = "tool_registered"
    PAYLOAD_VALIDATED = "payload_validated"
    POLICY_ALLOW_REQUIRED = "policy_allow_required"


class ToolPostcondition(str, Enum):
    STRUCTURED_OUTPUT = "structured_output"
    OUTPUT_SCHEMA_VALIDATED = "output_schema_validated"


class ToolSideEffect(str, Enum):
    NONE = "none"
    READ_DISK_USAGE = "read_disk_usage"
    READ_SYSTEM_METADATA = "read_system_metadata"


class DiskInfoStatus(str, Enum):
    OK = "ok"
    ERROR = "error"


class EchoPayload(StrictArtifactModel):
    text: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("text must not be blank")
        return normalized


class DiskInfoPayload(StrictArtifactModel):
    path: str | None = None

    @field_validator("path")
    @classmethod
    def path_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None

        normalized = value.strip()
        if not normalized:
            raise ValueError("path must not be blank")
        return normalized


class SystemInfoPayload(StrictArtifactModel):
    pass


class EchoOutput(StrictArtifactModel):
    echo: EchoPayload
    requested_by: str | None
    request_id: str | None


class DiskInfoData(StrictArtifactModel):
    path: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    total_gb: float
    used_gb: float
    free_gb: float
    free_percent: float
    os: str
    platform_details: str


class DiskInfoOutput(StrictArtifactModel):
    status: DiskInfoStatus
    message: str = Field(min_length=1)
    data: DiskInfoData


class SystemInfoOutput(StrictArtifactModel):
    requested_by: str | None
    request_id: str | None
    os: str
    os_version: str
    hostname: str
    machine: str
    processor: str


PAYLOAD_MODELS: dict[str, type[BaseModel]] = {
    "echo": EchoPayload,
    "disk_info": DiskInfoPayload,
    "system_info": SystemInfoPayload,
}
OUTPUT_MODELS: dict[str, type[BaseModel]] = {
    "echo": EchoOutput,
    "disk_info": DiskInfoOutput,
    "system_info": SystemInfoOutput,
}
TOOL_PRECONDITIONS: dict[str, list[ToolPrecondition]] = {
    "echo": [
        ToolPrecondition.AUTHENTICATED_CONTEXT,
        ToolPrecondition.TOOL_REGISTERED,
        ToolPrecondition.PAYLOAD_VALIDATED,
        ToolPrecondition.POLICY_ALLOW_REQUIRED,
    ],
    "disk_info": [
        ToolPrecondition.AUTHENTICATED_CONTEXT,
        ToolPrecondition.TOOL_REGISTERED,
        ToolPrecondition.PAYLOAD_VALIDATED,
        ToolPrecondition.POLICY_ALLOW_REQUIRED,
    ],
    "system_info": [
        ToolPrecondition.AUTHENTICATED_CONTEXT,
        ToolPrecondition.TOOL_REGISTERED,
        ToolPrecondition.PAYLOAD_VALIDATED,
        ToolPrecondition.POLICY_ALLOW_REQUIRED,
    ],
}


class ToolContractArtifact(StrictArtifactModel):
    name: ToolName
    input_schema: StructuredData
    output_schema: StructuredData
    preconditions: list[ToolPrecondition] = Field(min_length=1)
    postconditions: list[ToolPostcondition] = Field(min_length=1)
    side_effects: list[ToolSideEffect] = Field(min_length=1)
    version: Literal["tool_contract.v1"] = "tool_contract.v1"

    @model_validator(mode="after")
    def validate_side_effects(self) -> "ToolContractArtifact":
        if ToolSideEffect.NONE in self.side_effects and len(self.side_effects) > 1:
            raise ValueError("side_effects cannot combine none with real side effects")
        return self


def ensure_known_tool_name(tool_name: str) -> ToolName:
    if tool_name not in KNOWN_TOOL_NAMES:
        raise ValueError(f"unknown tool_name: {tool_name}")
    return cast(ToolName, tool_name)


def validate_tool_payload(tool_name: str, payload: dict | None) -> StructuredData:
    tool_name = ensure_known_tool_name(tool_name)
    payload_model = PAYLOAD_MODELS[tool_name]
    validated_payload = payload_model.model_validate(payload or {})
    return validated_payload.model_dump(mode="json", exclude_none=True)


def validate_tool_output(tool_name: str, output: dict) -> StructuredData:
    tool_name = ensure_known_tool_name(tool_name)
    output_model = OUTPUT_MODELS[tool_name]
    validated_output = output_model.model_validate(output)
    return validated_output.model_dump(mode="json")


def expected_output_schema(tool_name: str) -> StructuredData:
    tool_name = ensure_known_tool_name(tool_name)
    return OUTPUT_MODELS[tool_name].model_json_schema()


def action_preconditions(tool_name: str) -> list[ToolPrecondition]:
    tool_name = ensure_known_tool_name(tool_name)
    return list(TOOL_PRECONDITIONS[tool_name])
