from pydantic import BaseModel, ConfigDict, Field


class PaperlessDocumentRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: int = Field(ge=1)
    title: str
    created: str | None
    added: str | None
    original_file_name: str | None
    source_url: str


class PaperlessDocumentLinkWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: int = Field(ge=1)
