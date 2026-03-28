"""Law module representing legal statutes."""

from __future__ import annotations


class Law:
    """Represents a legal statute with an article number and severity level."""

    def __init__(
        self,
        article: int,
        severity: int = 1,
        desc: str = ""
    ) -> None:
        self._article: int = article
        self._desc: str = desc
        self._severity: int = severity
        # Validate severity on initialization
        if severity < 1 or severity > 5:
            raise ValueError("Severity must be between 1 and 5")

    @property
    def article(self) -> int:
        """Return the article number."""
        return self._article

    @property
    def desc(self) -> str:
        """Return the law description."""
        return self._desc

    @desc.setter
    def desc(self, value: str) -> None:
        """Set the law description."""
        self._desc = value

    @property
    def severity(self) -> int:
        """Return the severity level (1-5)."""
        return self._severity

    @severity.setter
    def severity(self, value: int) -> None:
        """Set the severity level with validation."""
        if not isinstance(value, int):
            raise TypeError("Severity must be an integer")
        if value < 1 or value > 5:
            raise ValueError("Severity must be between 1 and 5")
        self._severity = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Law):
            return NotImplemented
        return self._article == other._article

    def __hash__(self) -> int:
        return hash(self._article)

    def __repr__(self) -> str:
        return f"Law(article={self._article}, severity={self._severity})"

    def __str__(self) -> str:
        return f"Article {self._article}: Severity {self._severity}"
