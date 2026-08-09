from typing import Protocol

from devclean.domain.entities.audit_report import AuditReport


class AuditRepository(Protocol):
    """
    Contract for persisting and retrieving audit reports.
    """

    def save(self, report: AuditReport) -> None:
        """Persist a newly generated audit report."""
        ...
        
    def get_latest(self) -> AuditReport | None:
        """Retrieve the most recent audit report."""
        ...
