import typer
import logging
import json
import platform
from pathlib import Path
from typing import Optional

from devclean.domain.entities.scan_context import ScanContext
from devclean.domain.entities.cleanup_policy import ConservativePolicy, BalancedPolicy, AggressivePolicy
from devclean.domain.enums.cleanup import CleanupMode
from devclean.application.use_cases.scan import ScanUseCase
from devclean.application.events.event_bus import EventBus
from devclean.application.analyzers.registry import AnalyzerRegistry
from devclean.application.analyzers.pipeline import AnalyzerPipeline
from devclean.application.cleanup.recommendation_engine import RecommendationEngine
from devclean.application.cleanup.planner import CleanupPlanner
from devclean.infrastructure.cleanup.executor import CleanupExecutor
from devclean.infrastructure.logging.audit_logger import ExecutionHistoryLogger
from devclean.infrastructure.config.settings import Settings

# Analyzers (fallback for direct registration if needed, but registry handles loading via entry points now)
from devclean.infrastructure.python.analyzer import PythonAnalyzer
from devclean.infrastructure.chrome.analyzer import ChromeAnalyzer
from devclean.infrastructure.docker.analyzer import DockerAnalyzer
from devclean.infrastructure.wsl.analyzer import WSLAnalyzer

# CLI specifics
from devclean.presentation.cli.presenter import ConsolePresenter
from devclean.presentation.cli.progress import ProgressSubscriber
from devclean.presentation.cli.html_report import HTMLReportGenerator
from devclean.presentation.cli.exit_codes import ExitCode
from devclean.presentation.formatters.json_encoder import DevCleanJSONEncoder

app = typer.Typer(help="DevClean: Intelligent Storage Auditor")
presenter = ConsolePresenter()

# Load layered settings
try:
    settings = Settings.load()
except Exception:
    settings = Settings()

def _build_pipeline(event_bus: EventBus) -> AnalyzerRegistry:
    registry = AnalyzerRegistry()
    # Ensure built-ins are registered even if entry points fail
    registry.register(PythonAnalyzer())
    registry.register(ChromeAnalyzer())
    registry.register(DockerAnalyzer())
    registry.register(WSLAnalyzer())
    
    # Load plugins via entry points
    registry.load_plugins()
    registry.freeze()
    return registry

def _handle_json_output(data, json_fmt: bool, ndjson_fmt: bool):
    if json_fmt:
        print(json.dumps(data, cls=DevCleanJSONEncoder, indent=2))
        return True
    if ndjson_fmt:
        if "summary" in data:
            print(json.dumps({"summary": data["summary"]}, cls=DevCleanJSONEncoder))
        if "items" in data:
            for item in data["items"]:
                print(json.dumps({"item": item}, cls=DevCleanJSONEncoder))
        if "recommendations" in data:
            for rec in data["recommendations"]:
                print(json.dumps({"recommendation": rec}, cls=DevCleanJSONEncoder))
        return True
    return False

@app.command()
def scan(
    path: Path = typer.Argument(Path.home(), help="The root path to scan"),
    json_fmt: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
    ndjson_fmt: bool = typer.Option(False, "--ndjson", help="Output streaming NDJSON"),
):
    """Scan the system for reclaimable space."""
    try:
        event_bus = EventBus()
        progress = ProgressSubscriber()
        
        if not (json_fmt or ndjson_fmt):
            event_bus.subscribe_all(progress.handle)

        registry = _build_pipeline(event_bus)
        pipeline = AnalyzerPipeline(registry, event_bus)
        use_case = ScanUseCase(pipeline)
        
        exclude_paths = tuple(Path(e) for e in settings.scan.exclude)
        context = ScanContext(target_path=path, exclude_paths=exclude_paths)

        if json_fmt or ndjson_fmt:
            result = use_case.execute(context)
            _handle_json_output({"summary": result.report.summary, "items": result.report.items}, json_fmt, ndjson_fmt)
        else:
            with progress.run():
                result = use_case.execute(context)
            presenter.show_scan_summary(result.report)
            
        raise typer.Exit(code=ExitCode.SUCCESS)
        
    except typer.Exit:
        raise
    except Exception as e:
        if not (json_fmt or ndjson_fmt):
            presenter.console.print(f"[bold red]Scan failed: {e}[/bold red]")
        raise typer.Exit(code=ExitCode.EXECUTION_FAILURE)


@app.command()
def cleanup(
    path: Path = typer.Argument(Path.home(), help="The root path to scan"),
    preview: bool = typer.Option(False, "--preview", help="Show cleanup preview without executing"),
    policy_name: str = typer.Option(None, "--policy", help="Policy to use: conservative, balanced, aggressive"),
    json_fmt: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
    ndjson_fmt: bool = typer.Option(False, "--ndjson", help="Output streaming NDJSON"),
):
    """Run a scan and interactively clean up space."""
    try:
        policy_name = policy_name or settings.cleanup.policy
        event_bus = EventBus()
        progress = ProgressSubscriber()
        
        if not (json_fmt or ndjson_fmt):
            event_bus.subscribe_all(progress.handle)

        registry = _build_pipeline(event_bus)
        pipeline = AnalyzerPipeline(registry, event_bus)
        use_case = ScanUseCase(pipeline)
        
        exclude_paths = tuple(Path(e) for e in settings.scan.exclude)
        context = ScanContext(target_path=path, exclude_paths=exclude_paths)

        if json_fmt or ndjson_fmt:
            result = use_case.execute(context)
        else:
            with progress.run():
                result = use_case.execute(context)
            
        engine = RecommendationEngine()
        decisions = engine.generate_recommendations(result.report)
        
        match policy_name.lower():
            case "conservative": policy = ConservativePolicy
            case "aggressive": policy = AggressivePolicy
            case _: policy = BalancedPolicy
            
        planner = CleanupPlanner()
        plan = planner.create_plan(decisions, policy)
        
        if json_fmt or ndjson_fmt:
            actions_data = [a.decision for a in plan.actions]
            _handle_json_output({
                "summary": result.report.summary,
                "items": result.report.items,
                "recommendations": actions_data
            }, json_fmt, ndjson_fmt)
            if preview and plan.actions:
                raise typer.Exit(code=ExitCode.CLEANUP_ACTIONS_AVAILABLE)
            raise typer.Exit(code=ExitCode.SUCCESS)
            
        presenter.show_cleanup_preview(plan)
        
        if preview:
            if plan.actions:
                raise typer.Exit(code=ExitCode.CLEANUP_ACTIONS_AVAILABLE)
            raise typer.Exit(code=ExitCode.SUCCESS)
            
        selected_actions = presenter.prompt_interactive_selection(plan.actions)
        if not selected_actions:
            raise typer.Exit(code=ExitCode.SUCCESS)
            
        if not presenter.prompt_confirmation(plan, selected_actions):
            raise typer.Exit(code=ExitCode.SUCCESS)
            
        executor = CleanupExecutor(allowed_roots=(path,))
        from devclean.domain.entities.cleanup_plan import CleanupPlan
        import uuid
        filtered_plan = CleanupPlan(
            id=uuid.uuid4(),
            actions=tuple(selected_actions),
            estimated_reclaimable_bytes=sum(a.decision.item.size_bytes for a in selected_actions),
            risk_summary=plan.risk_summary
        )
        
        exec_report = executor.execute(filtered_plan, mode=CleanupMode.EXECUTE)
        
        logger = ExecutionHistoryLogger()
        logger.log_execution(filtered_plan, exec_report, CleanupMode.EXECUTE, policy_name)
        
        presenter.show_execution_results(
            success_count=exec_report.succeeded,
            failure_count=exec_report.failed,
            bytes_freed=exec_report.bytes_freed
        )
        raise typer.Exit(code=ExitCode.SUCCESS)

    except typer.Exit:
        raise
    except PermissionError:
        if not (json_fmt or ndjson_fmt):
            presenter.console.print("[bold red]Permission denied during cleanup.[/bold red]")
        raise typer.Exit(code=ExitCode.PERMISSION_REQUIRED)
    except typer.Exit:
        raise
    except Exception as e:
        if not (json_fmt or ndjson_fmt):
            presenter.console.print(f"[bold red]Cleanup failed: {e}[/bold red]")
        raise typer.Exit(code=ExitCode.EXECUTION_FAILURE)

@app.command()
def report(
    path: Path = typer.Argument(Path.home(), help="The root path to scan"),
    html: Optional[str] = typer.Option(None, "--html", help="Path to save HTML report"),
    json_out: Optional[str] = typer.Option(None, "--json", help="Path to save JSON report"),
):
    """Generate reports of findings."""
    try:
        # If neither is provided, fallback to default format from config
        if not html and not json_out:
            if settings.reports.default_format == "html":
                html = "report.html"
            elif settings.reports.default_format == "json":
                json_out = "report.json"
            else:
                html = "report.html"

        event_bus = EventBus()
        progress = ProgressSubscriber()
        event_bus.subscribe_all(progress.handle)

        registry = _build_pipeline(event_bus)
        pipeline = AnalyzerPipeline(registry, event_bus)
        use_case = ScanUseCase(pipeline)
        
        exclude_paths = tuple(Path(e) for e in settings.scan.exclude)
        context = ScanContext(target_path=path, exclude_paths=exclude_paths)

        with progress.run():
            result = use_case.execute(context)
            
        engine = RecommendationEngine()
        decisions = engine.generate_recommendations(result.report)
        planner = CleanupPlanner()
        plan = planner.create_plan(decisions, BalancedPolicy)
        
        if html:
            generator = HTMLReportGenerator()
            html_content = generator.generate(result, plan)
            out_path = Path(html)
            out_path.write_text(html_content, encoding="utf-8")
            presenter.console.print(f"[bold green]HTML Report generated at {out_path.absolute()}[/bold green]")
            
        if json_out:
            out_path = Path(json_out)
            data = {
                "schema_version": "1.0",
                "generated_at": result.report.summary.total_size_bytes, # simplistic mapping
                "scan_id": str(result.report.items[0].id) if result.report.items else "none",
                "summary": result.report.summary,
                "items": result.report.items
            }
            out_path.write_text(json.dumps(data, cls=DevCleanJSONEncoder, indent=2), encoding="utf-8")
            presenter.console.print(f"[bold green]JSON Report generated at {out_path.absolute()}[/bold green]")

        raise typer.Exit(code=ExitCode.SUCCESS)
    except typer.Exit:
        raise
    except Exception as e:
        presenter.console.print(f"[bold red]Report generation failed: {e}[/bold red]")
        raise typer.Exit(code=ExitCode.EXECUTION_FAILURE)

@app.command()
def history(
    json_fmt: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
):
    """View past cleanup executions from the audit log."""
    try:
        log_dir = Path.home() / ".devclean" / "history"
        if not log_dir.exists():
            if not json_fmt:
                presenter.console.print("No history found.")
            raise typer.Exit(code=ExitCode.SUCCESS)
            
        entries = []
        parsed = []
        for log_file in sorted(log_dir.glob("*.json"), reverse=True):
            content = log_file.read_text(encoding="utf-8")
            entries.append(content)
            parsed.append(json.loads(content))
            
        if json_fmt:
            print(json.dumps(parsed, indent=2))
        else:
            presenter.show_history(entries)
            
        raise typer.Exit(code=ExitCode.SUCCESS)
    except typer.Exit:
        raise
    except Exception as e:
        raise typer.Exit(code=ExitCode.EXECUTION_FAILURE)

@app.command()
def explain(category: str):
    """Explain the provenance, risk, and rollback strategy for a cleanup category."""
    presenter.show_explanation(category)
    raise typer.Exit(code=ExitCode.SUCCESS)

@app.command()
def version(verbose: bool = typer.Option(False, "--verbose", help="Show diagnostic version details")):
    """Show version information."""
    ver_str = "0.6.0" # Hardcoded for now
    if not verbose:
        print(f"DevClean {ver_str}")
    else:
        registry = AnalyzerRegistry()
        registry.load_plugins()
        plugins = [a.metadata.name for a in registry.get_all()]
        failed = registry.get_failed_plugins()
        
        info = {
            "Version": ver_str,
            "Python": platform.python_version(),
            "Platform": platform.platform(),
            "Config": str(settings.config_path) if settings.config_path else "None",
            "Plugins Loaded": ", ".join(plugins),
            "Plugins Failed": str(failed) if failed else "None",
            "Schema Version": "1.0"
        }
        for k, v in info.items():
            print(f"{k}: {v}")

@app.command()
def diff(before: Path = typer.Argument(..., help="Path to 'before' JSON report"), after: Path = typer.Argument(..., help="Path to 'after' JSON report")):
    """Diff two JSON reports to show reclaimed space and changed findings."""
    from devclean.application.reporting.differ import ReportDiffer
    try:
        b_data = json.loads(before.read_text(encoding="utf-8"))
        a_data = json.loads(after.read_text(encoding="utf-8"))
        
        differ = ReportDiffer()
        result = differ.diff(b_data, a_data)
        
        from rich.table import Table
        
        def format_size(size: int) -> str:
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024
            return f"{size:.2f} PB"
        
        table = Table(title="Report Diff Summary")
        table.add_column("Metric")
        table.add_column("Value", justify="right")
        
        table.add_row("Total Reclaimed Space", f"[bold green]{format_size(result.reclaimed_bytes)}[/bold green]")
        table.add_row("Removed Findings", f"{result.removed_count} ({format_size(result.removed_bytes)})")
        table.add_row("New Findings", f"{result.new_count} ({format_size(result.new_bytes)})")
        table.add_row("Size Increased", str(result.changed_increased_count))
        table.add_row("Size Decreased", str(result.changed_decreased_count))
        
        presenter.console.print(table)
        
        if result.categories:
            cat_table = Table(title="Reclaimed by Category")
            cat_table.add_column("Category")
            cat_table.add_column("Space Reclaimed", justify="right")
            for cat, b in sorted(result.categories.items(), key=lambda x: x[1], reverse=True):
                cat_table.add_row(cat, format_size(b))
            presenter.console.print(cat_table)
            
        raise typer.Exit(code=ExitCode.SUCCESS)
    except typer.Exit:
        raise
    except Exception as e:
        presenter.console.print(f"[bold red]Diff failed: {e}[/bold red]")
        raise typer.Exit(code=ExitCode.EXECUTION_FAILURE)

@app.command()
def doctor():
    """Run diagnostics to verify system health, permissions, and plugin integrity."""
    from rich.table import Table
    import os
    
    registry = AnalyzerRegistry()
    registry.load_plugins()
    failed = registry.get_failed_plugins()
    
    log_dir = Path.home() / ".devclean" / "history"
    log_writable = os.access(log_dir, os.W_OK) if log_dir.exists() else os.access(log_dir.parent, os.W_OK)
    
    # Simple admin check (windows)
    import ctypes
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        
    table = Table(title="DevClean Diagnostics")
    table.add_column("Category", style="cyan")
    table.add_column("Check", style="magenta")
    table.add_column("Status", justify="right")
    
    table.add_row("Environment", "Python Version", platform.python_version())
    table.add_row("Environment", "Config Loaded", str(settings.config_path) if settings.config_path else "[yellow]Defaults Only[/yellow]")
    table.add_row("Permissions", "History Writable", "[green]Yes[/green]" if log_writable else "[red]No[/red]")
    table.add_row("Permissions", "Administrator", "[green]Yes[/green]" if is_admin else "[yellow]No[/yellow]")
    table.add_row("Plugins", "Built-in Loaded", "4")
    table.add_row("Plugins", "External Loaded", str(len(registry.get_all()) - 4))
    table.add_row("Plugins", "Failed Plugins", f"[red]{len(failed)}[/red]" if failed else "[green]0[/green]")
    
    presenter.console.print(table)
    if failed:
        presenter.console.print("\n[bold red]Failed Plugins:[/bold red]")
        for p, err in failed.items():
            presenter.console.print(f"  {p}: {err}")
            
    raise typer.Exit(code=ExitCode.SUCCESS)

if __name__ == "__main__":
    app()
