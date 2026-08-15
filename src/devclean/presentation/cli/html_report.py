import platform
from datetime import datetime
from typing import Optional

from devclean.domain.entities.scan_result import ScanResult
from devclean.domain.entities.cleanup_plan import CleanupPlan
from devclean.domain.enums.risk_level import RiskLevel

class HTMLReportGenerator:
    """Generates a dedicated HTML report from audit results."""
    
    def _format_bytes(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def _risk_color(self, risk: RiskLevel) -> str:
        match risk:
            case RiskLevel.SAFE: return "#28a745"
            case RiskLevel.LOW: return "#ffc107"
            case RiskLevel.MODERATE: return "#fd7e14"
            case RiskLevel.HIGH: return "#dc3545"
            case _: return "#6c757d"

    def generate(self, result: ScanResult, plan: Optional[CleanupPlan] = None) -> str:
        summary = result.report.summary
        total_freed_est = plan.estimated_reclaimable_bytes if plan else summary.reclaimable_size_bytes
        
        # Build Findings HTML
        findings_html = "<ul>"
        for item in result.report.items:
            color = self._risk_color(item.risk_level)
            findings_html += f"""
                <li style="margin-bottom: 8px;">
                    <strong>{item.description}</strong> ({self._format_bytes(item.size_bytes)})
                    <span style="color: white; background-color: {color}; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; margin-left: 8px;">
                        {item.risk_level.name}
                    </span><br>
                    <small style="color: #666;">{item.path}</small>
                </li>
            """
        findings_html += "</ul>"
        
        # Build Plan HTML
        plan_html = ""
        if plan:
            plan_html = "<h3>Cleanup Recommendations</h3><table style='width: 100%; border-collapse: collapse;'>"
            plan_html += "<tr style='background: #f8f9fa; border-bottom: 2px solid #dee2e6;'><th style='text-align: left; padding: 8px;'>Action</th><th style='text-align: right; padding: 8px;'>Size</th><th style='text-align: left; padding: 8px;'>Rollback</th></tr>"
            for action in plan.actions:
                plan_html += f"""
                    <tr style='border-bottom: 1px solid #dee2e6;'>
                        <td style='padding: 8px;'>{action.decision.recommendation.operation.name.replace('_', ' ').capitalize()} {action.decision.item.description}</td>
                        <td style='text-align: right; padding: 8px;'>{self._format_bytes(action.decision.item.size_bytes)}</td>
                        <td style='padding: 8px;'>{action.decision.recommendation.rollback.name.replace('_', ' ').capitalize()}</td>
                    </tr>
                """
            plan_html += "</table>"
        else:
            plan_html = "<p>No cleanup plan generated.</p>"

        # Template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DevClean Audit Report</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 1000px; margin: 0 auto; padding: 2rem; }}
                h1, h2, h3 {{ color: #2c3e50; border-bottom: 1px solid #eee; padding-bottom: 0.3rem; }}
                .summary-card {{ background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; display: flex; justify-content: space-between; }}
                .stat-box {{ text-align: center; }}
                .stat-value {{ font-size: 2rem; font-weight: bold; color: #007bff; }}
                .stat-label {{ color: #6c757d; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }}
                .section {{ margin-bottom: 3rem; }}
            </style>
        </head>
        <body>
            <h1>DevClean Audit Report</h1>
            <p>Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            
            <div class="summary-card">
                <div class="stat-box">
                    <div class="stat-value">{summary.total_items}</div>
                    <div class="stat-label">Items Found</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{self._format_bytes(summary.total_size_bytes)}</div>
                    <div class="stat-label">Total Size Scanned</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" style="color: #28a745;">{self._format_bytes(total_freed_est)}</div>
                    <div class="stat-label">Potential Reclaim</div>
                </div>
            </div>
            
            <div class="section">
                <h2>System Information</h2>
                <p>
                    <strong>OS:</strong> {platform.system()} {platform.release()}<br>
                    <strong>Machine:</strong> {platform.machine()}<br>
                    <strong>Python:</strong> {platform.python_version()}
                </p>
            </div>
            
            <div class="section">
                <h2>Cleanup Preview</h2>
                {plan_html}
            </div>
            
            <div class="section">
                <h2>Detailed Findings</h2>
                {findings_html}
            </div>
            
        </body>
        </html>
        """
        return html
