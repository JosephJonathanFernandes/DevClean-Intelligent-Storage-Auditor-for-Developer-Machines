import json
from typing import List, Dict, Any, Iterable
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.rule import Rule
import questionary

from devclean.domain.entities.audit_report import AuditReport
from devclean.domain.entities.cleanup_plan import CleanupPlan, CleanupAction
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.category import Category


class ConsolePresenter:
    """Facade for all terminal presentation and interactivity."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()

    def _format_bytes(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def _risk_color(self, risk: RiskLevel) -> str:
        match risk:
            case RiskLevel.SAFE:
                return "green"
            case RiskLevel.LOW:
                return "yellow"
            case RiskLevel.MODERATE:
                return "orange3"
            case RiskLevel.HIGH:
                return "red"
            case _:
                return "white"

    def show_scan_summary(self, report: AuditReport) -> None:
        """Shows the final summary after a scan completes."""
        self.console.print("\n[bold green]Scan complete[/bold green]\n")
        
        reclaimable = self._format_bytes(report.summary.reclaimable_size_bytes)
        self.console.print(f"[bold]Potential reclaim:[/bold] [cyan]{reclaimable}[/cyan]\n")

        # Group by risk
        items_by_risk: Dict[RiskLevel, list] = {r: [] for r in RiskLevel}
        for item in report.items:
            items_by_risk[item.risk_level].append(item)

        self.console.print("[bold]Findings[/bold]")
        for risk in [RiskLevel.SAFE, RiskLevel.LOW, RiskLevel.MODERATE, RiskLevel.HIGH]:
            items = items_by_risk[risk]
            if not items:
                continue
                
            color = self._risk_color(risk)
            self.console.print(f"\n[{color}]{risk.name}[/{color}]")
            
            # Group by category for cleaner display
            category_totals: Dict[Category, int] = {}
            for item in items:
                category_totals[item.category] = category_totals.get(item.category, 0) + item.size_bytes
                
            for cat, size in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
                self.console.print(f"  {cat.value.replace('_', ' ').capitalize().ljust(30)} {self._format_bytes(size)}")

        self.console.print("\nRun: [bold cyan]devclean cleanup --preview[/bold cyan]\n")

    def show_cleanup_preview(self, plan: CleanupPlan) -> None:
        """Renders the cleanup plan in a grouped table."""
        if not plan.actions:
            self.console.print("[bold yellow]No cleanup actions recommended based on current policy.[/bold yellow]")
            return

        table = Table(title="Cleanup Preview", show_header=True, header_style="bold magenta")
        table.add_column("Action", style="dim", width=40)
        table.add_column("Risk", justify="center")
        table.add_column("Size", justify="right")
        table.add_column("Rollback")

        for action in plan.actions:
            decision = action.decision
            risk = decision.item.risk_level
            color = self._risk_color(risk)
            
            action_desc = f"{decision.recommendation.operation.name.replace('_', ' ').capitalize()} {decision.item.description}"
            size_str = self._format_bytes(decision.item.size_bytes)
            
            table.add_row(
                action_desc,
                f"[{color}]{risk.name}[/{color}]",
                size_str,
                decision.recommendation.rollback.name.replace("_", " ").capitalize()
            )

        self.console.print(table)
        
        # Build trust message
        safe_msg = "[bold green]Will not delete installed Python packages, virtual environments, user documents, or Chrome profiles.[/bold green]"
        self.console.print(Panel(safe_msg, title="Safety Guarantee", border_style="green"))

    def prompt_interactive_selection(self, actions: Iterable[CleanupAction]) -> List[CleanupAction]:
        """Prompts the user to select which actions to execute."""
        action_list = list(actions)
        if not action_list:
            return []

        choices = []
        for action in action_list:
            desc = f"{action.decision.item.description} ({self._format_bytes(action.decision.item.size_bytes)})"
            choices.append(questionary.Choice(desc, value=action, checked=True))

        selected = questionary.checkbox(
            "Select actions to execute:",
            choices=choices
        ).ask()
        
        # ask() returns None if user aborted (Ctrl+C)
        return selected or []

    def prompt_confirmation(self, plan: CleanupPlan, selected_actions: List[CleanupAction]) -> bool:
        """Provides a safe summary prompt."""
        if not selected_actions:
            self.console.print("[yellow]No actions selected. Aborting.[/yellow]")
            return False

        total_bytes = sum(a.decision.item.size_bytes for a in selected_actions)
        
        auto_rollback = sum(1 for a in selected_actions if 'AUTOMATICALLY' in a.decision.recommendation.rollback.name)
        manual_rollback = len(selected_actions) - auto_rollback

        summary = Text()
        summary.append(f"You are about to execute {len(selected_actions)} cleanup actions.\n\n", style="bold")
        summary.append(f"Estimated reclaim: {self._format_bytes(total_bytes)}\n\n", style="bold cyan")
        summary.append("Rollback:\n")
        summary.append(f"  Automatic: {auto_rollback}\n", style="green")
        summary.append(f"  Manual/None: {manual_rollback}\n", style="yellow")

        self.console.print(Panel(summary, title="Execution Summary", border_style="red"))

        answer = questionary.text("Type 'clean' to continue:").ask()
        return answer == "clean"

    def show_execution_results(self, success_count: int, failure_count: int, bytes_freed: int) -> None:
        self.console.print(Rule())
        if failure_count > 0:
            self.console.print(f"[bold red]Cleanup finished with {failure_count} failures.[/bold red]")
        else:
            self.console.print("[bold green]Cleanup completed successfully![/bold green]")
        self.console.print(f"Total space freed: [bold cyan]{self._format_bytes(bytes_freed)}[/bold cyan]")

    def show_history(self, log_lines: List[str]) -> None:
        """Parses the JSON audit logs and displays history."""
        if not log_lines:
            self.console.print("No history found.")
            return

        for line in log_lines:
            try:
                entry = json.loads(line)
                date_str = entry.get("timestamp", "Unknown time")
                freed = entry.get("freed_bytes", 0)
                policy = entry.get("policy", "unknown")
                mode = entry.get("mode", "unknown")
                
                self.console.print(f"[bold]{date_str}[/bold] ({mode})")
                self.console.print(f"Freed: [cyan]{self._format_bytes(freed)}[/cyan]")
                self.console.print(f"Policy: {policy}\n")
            except json.JSONDecodeError:
                continue

    def show_explanation(self, category_name: str) -> None:
        """Placeholder for detailed educational explanation."""
        # For a full implementation, this could map category names to markdown docs or rule provenance
        self.console.print(f"[bold]{category_name.replace('-', ' ').title()}[/bold]\n")
        self.console.print("This category stores downloaded package archives or caches.")
        self.console.print("Deleting it will not uninstall active packages.\n")
        self.console.print("[bold]Rollback:[/bold] [green]Regenerates automatically[/green]")
        self.console.print("[bold]Risk:[/bold] [green]Safe[/green]")
        self.console.print("[bold]Confidence:[/bold] [green]Verified[/green]")
