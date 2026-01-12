from pydantic import BaseModel, Field
from typing import Optional


class ExtractedEntities(BaseModel):
    """Entity schema for GPT-4o-mini structured outputs."""

    people: list[str] = Field(
        default_factory=list,
        description="Names of people, authors, experts, or roles mentioned in the text"
    )
    organizations: list[str] = Field(
        default_factory=list,
        description="Companies, institutions, agencies, or organizations"
    )
    locations: list[str] = Field(
        default_factory=list,
        description="Places, cities, countries, regions, or addresses"
    )
    dates: list[str] = Field(
        default_factory=list,
        description="Temporal references including dates, years, periods, or time ranges"
    )
    topics: list[str] = Field(
        default_factory=list,
        description="Main subjects, themes, or key concepts discussed"
    )
    technical_terms: list[str] = Field(
        default_factory=list,
        description="Domain-specific terminology, acronyms, or specialized vocabulary"
    )

    def to_searchable_text(self) -> str:
        """Convert entities to searchable text for BM25 indexing."""
        parts = []
        if self.people:
            parts.append(" ".join(self.people))
        if self.organizations:
            parts.append(" ".join(self.organizations))
        if self.locations:
            parts.append(" ".join(self.locations))
        if self.dates:
            parts.append(" ".join(self.dates))
        if self.topics:
            parts.append(" ".join(self.topics))
        if self.technical_terms:
            parts.append(" ".join(self.technical_terms))
        return " ".join(parts)

    def is_empty(self) -> bool:
        """Check if no entities were extracted."""
        return not any([
            self.people,
            self.organizations,
            self.locations,
            self.dates,
            self.topics,
            self.technical_terms
        ])


class EntityFilters(BaseModel):
    """Filters for entity-based search."""

    people: Optional[list[str]] = None
    organizations: Optional[list[str]] = None
    locations: Optional[list[str]] = None
    dates: Optional[list[str]] = None
    topics: Optional[list[str]] = None
    technical_terms: Optional[list[str]] = None

    def has_filters(self) -> bool:
        """Check if any filters are set."""
        return any([
            self.people,
            self.organizations,
            self.locations,
            self.dates,
            self.topics,
            self.technical_terms
        ])
