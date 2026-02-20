"""Base classes for batch jobs."""
from dataclasses import dataclass, field
from typing import List


@dataclass
class BatchJobResult:
    """Result of a batch job execution."""

    success: bool
    processed_count: int = 0
    failed_count: int = 0
    errors: List[str] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "errors": self.errors,
            "message": self.message,
        }
