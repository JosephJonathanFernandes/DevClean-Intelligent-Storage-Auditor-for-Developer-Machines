import typer
import logging
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

# Analyzers
from devclean.infrastructure.python.analyzer import PythonAnalyzer
from devclean.infrastructure.chrome.analyzer import ChromeAnalyzer
from devclean.infrastructure.docker.analyzer import DockerAnalyzer
from devclean.infrastructure.wsl.analyzer import WSLAnalyzer

# CLI specifics
from devclean.presentation.cli.presenter import ConsolePresenter
from devclean.presentation.cli.progress import ProgressSubscriber
from devclean.presentation.cli.html_report import HTMLReportGenerator

app = typer.Typer(help="DevClean: Intelligent Storage Auditor")
presenter = ConsolePresenter()

def _build_pipeline(event_bus: EventBus) -> AnalyzerPipeline:
    registry = AnalyzerRegistry()
    registry.register(PythonAnalyzer())
    registry.register(ChromeAnalyzer())
    registry.register(DockerAnalyzer())
    registry.register(WSLAnalyzer())
    registry.freeze()
    return AnalyzerPipeline(registry, event_bus)

@app.command()
def scan(
    path: Path = typer.Argument(Path.home(), help="The root path to scan"),
):
    """Scan the system for reclaimable space."""
    event_bus = EventBus()
    progress = ProgressSubscriber()
    event_bus.subscribe_all(progress.handle)

    pipeline = _build_pipeline(event_bus)
    use_case = ScanUseCase(pipeline)
    
    context = ScanContext(
        target_path=path,
        exclude_paths=()
    )

    with progress.run():
        result = use_case.execute(context)
        
    presenter.show_scan_summary(result.report)

@app.command()
def cleanup(
    path: Path = typer.Argument(Path.home(), help="The root path to scan"),
    preview: bool = typer.Option(False, "--preview", help="Show cleanup preview without executing"),
    policy_name: str = typer.Option("balanced", "--policy", help="Policy to use: conservative, balanced, aggressive"),
):
    """Run a scan and interactively clean up space."""
    # 1. Scan Phase
    event_bus = EventBus()
    progress = ProgressSubscriber()
    event_bus.subscribe_all(progress.handle)

    pipeline = _build_pipeline(event_bus)
    use_case = ScanUseCase(pipeline)
    
    context = ScanContext(target_path=path, exclude_paths=())

    with progress.run():
        result = use_case.execute(context)
        
    # 2. Recommendation & Planning Phase
    engine = RecommendationEngine()
    decisions = engine.generate_recommendations(result.report)
    
    match policy_name.lower():
        case "conservative": policy = ConservativePolicy
        case "aggressive": policy = AggressivePolicy
        case _: policy = BalancedPolicy
        
    planner = CleanupPlanner()
    plan = planner.create_plan(decisions, policy)
    
    presenter.show_cleanup_preview(plan)
    
    if preview:
        return
        
    # 3. Interactive Selection Phase
    selected_actions = presenter.prompt_interactive_selection(plan.actions)
    if not selected_actions:
        return
        
    # 4. Confirmation Phase
    if not presenter.prompt_confirmation(plan, selected_actions):
        return
        
    # 5. Execution Phase
    executor = CleanupExecutor(allowed_roots=(path,))
    # Re-build a filtered plan based on selection
    from devclean.domain.entities.cleanup_plan import CleanupPlan
    import uuid
    filtered_plan = CleanupPlan(
        id=uuid.uuid4(),
        actions=tuple(selected_actions),
        estimated_reclaimable_bytes=sum(a.decision.item.size_bytes for a in selected_actions),
        risk_summary=plan.risk_summary
    )
    
    exec_report = executor.execute(filtered_plan, mode=CleanupMode.EXECUTE)
    
    # 6. Audit Logging
    logger = ExecutionHistoryLogger()
    logger.log_execution(filtered_plan, exec_report, CleanupMode.EXECUTE, policy_name)
    
    presenter.show_execution_results(
        success_count=exec_report.succeeded,
        failure_count=exec_report.failed,
        bytes_freed=exec_report.bytes_freed
    )

@app.command()
def report(
    path: Path = typer.Argument(Path.home(), help="The root path to scan"),
    html: str = typer.Option("report.html", "--html", help="Path to save HTML report"),
):
    """Generate a dedicated HTML report of findings."""
    event_bus = EventBus()
    progress = ProgressSubscriber()
    event_bus.subscribe_all(progress.handle)

    pipeline = _build_pipeline(event_bus)
    use_case = ScanUseCase(pipeline)
    context = ScanContext(target_path=path, exclude_paths=())

    with progress.run():
        result = use_case.execute(context)
        
    engine = RecommendationEngine()
    decisions = engine.generate_recommendations(result.report)
    planner = CleanupPlanner()
    plan = planner.create_plan(decisions, BalancedPolicy)
    
    generator = HTMLReportGenerator()
    html_content = generator.generate(result, plan)
    
    out_path = Path(html)
    out_path.write_text(html_content, encoding="utf-8")
    presenter.console.print(f"[bold green]Report generated at {out_path.absolute()}[/bold green]")

@app.command()
def history():
    """View past cleanup executions from the audit log."""
    log_dir = Path.home() / ".devclean" / "history"
    if not log_dir.exists():
        presenter.console.print("No history found.")
        return
        
    entries = []
    for log_file in sorted(log_dir.glob("*.json"), reverse=True):
        entries.append(log_file.read_text(encoding="utf-8"))
        
    presenter.show_history(entries)

@app.command()
def explain(category: str):
    """Explain the provenance, risk, and rollback strategy for a cleanup category."""
    presenter.show_explanation(category)

if __name__ == "__main__":
    app()
