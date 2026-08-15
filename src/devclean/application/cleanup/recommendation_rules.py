import math
from typing import Protocol, List
from pathlib import Path

from devclean.domain.entities.audit_item import AuditItem
from devclean.domain.entities.recommendation import Recommendation
from devclean.domain.enums.category import Category
from devclean.domain.enums.risk_level import RiskLevel
from devclean.domain.enums.confidence_level import ConfidenceLevel
from devclean.domain.enums.cleanup import RollbackStrategy, CleanupOperation
from devclean.domain.enums.recommendation_reason import RecommendationReason

class RecommendationRule(Protocol):
    def applies(self, item: AuditItem) -> bool:
        ...

    def recommend(self, item: AuditItem) -> Recommendation:
        ...

    def score(self, item: AuditItem) -> tuple[float, dict[str, float]]:
        ...

    def reason(self, item: AuditItem) -> RecommendationReason:
        ...

# Base Rule class to provide standard scoring logic
class BaseRecommendationRule:
    def score(self, item: AuditItem) -> tuple[float, dict[str, float]]:
        score = 0.0
        breakdown = {}
        
        # 1. Size bonus (Logarithmic: more size = more priority, up to a cap)
        # 1GB = 1,000,000,000 bytes. log10(1B) = 9
        if item.size_bytes > 0:
            size_weight = min(10.0, math.log10(item.size_bytes))
            score += size_weight
            breakdown["size"] = size_weight
            
        # 2. Risk weight
        risk_weights = {
            RiskLevel.SAFE: 10.0,
            RiskLevel.LOW: 5.0,
            RiskLevel.MODERATE: 0.0,
            RiskLevel.HIGH: -5.0,
        }
        risk_weight = risk_weights.get(item.risk_level, 0.0)
        score += risk_weight
        breakdown["safety"] = risk_weight
        
        # 3. Confidence weight
        confidence_weights = {
            ConfidenceLevel.VERIFIED: 5.0,
            ConfidenceLevel.PROBABLE: 2.0,
            ConfidenceLevel.HEURISTIC: 0.0,
        }
        confidence_weight = confidence_weights.get(item.confidence, 0.0)
        score += confidence_weight
        breakdown["confidence"] = confidence_weight
        
        # 4. Rollback weight (Automatic = better)
        rec = self.recommend(item)
        rollback_weights = {
            RollbackStrategy.REGENERATES_AUTOMATICALLY: 5.0,
            RollbackStrategy.REQUIRES_REDOWNLOAD: 2.0,
            RollbackStrategy.ARCHIVE_AND_RESTORE: 0.0,
            RollbackStrategy.REQUIRES_MANUAL_RESTORE: -5.0,
            RollbackStrategy.NO_ROLLBACK_AVAILABLE: -10.0,
        }
        rollback_weight = rollback_weights.get(rec.rollback, 0.0)
        score += rollback_weight
        breakdown["rollback"] = rollback_weight
        
        return max(0.0, score), breakdown

    def reason(self, item: AuditItem) -> RecommendationReason:
        if item.size_bytes > 1_000_000_000 and item.risk_level == RiskLevel.SAFE:
            return RecommendationReason.LARGE_SAFE_RECLAIM
        if item.category in (Category.BROWSER_CACHE, Category.PYTHON_CACHE, Category.BUILD_ARTIFACT):
            return RecommendationReason.STALE_CACHE
        if item.category == Category.VENV:
            return RecommendationReason.UNUSED_ENVIRONMENT
        if "duplicate" in item.description.lower() or item.metadata.get("is_duplicate"):
            return RecommendationReason.DUPLICATE_RUNTIME
        if item.risk_level == RiskLevel.LOW or item.risk_level == RiskLevel.SAFE:
            return RecommendationReason.LOW_RISK_OPTIMIZATION
            
        return RecommendationReason.DEFAULT_RULE


class PipCacheRule(BaseRecommendationRule):
    def applies(self, item: AuditItem) -> bool:
        return item.category == Category.PYTHON_CACHE
        
    def recommend(self, item: AuditItem) -> Recommendation:
        return Recommendation(
            title="Purge pip download cache",
            explanation="This cache stores downloaded package archives. Deleting it will not uninstall installed Python packages.",
            safety_reason="Contains downloaded package archives only. Installed packages are not affected.",
            rollback=RollbackStrategy.REGENERATES_AUTOMATICALLY,
            operation=CleanupOperation.PURGE_CACHE,
            rollback_notes="Cache will regenerate automatically when downloading new packages.",
            command="python -m pip cache purge",
            files_affected=(item.path,)
        )

class VirtualenvRule(BaseRecommendationRule):
    def applies(self, item: AuditItem) -> bool:
        return item.category == Category.VENV
        
    def recommend(self, item: AuditItem) -> Recommendation:
        return Recommendation(
            title="Delete virtual environment",
            explanation="Python virtual environment.",
            safety_reason="Recreating a virtual environment requires reinstalling all packages from requirements.txt.",
            rollback=RollbackStrategy.REQUIRES_MANUAL_RESTORE,
            rollback_notes="Must run `python -m venv` and `pip install -r requirements.txt` to restore.",
            files_affected=(item.path,),
            operation=CleanupOperation.DELETE_DIRECTORY
        )

class CondaRule(BaseRecommendationRule):
    def applies(self, item: AuditItem) -> bool:
        return item.category == Category.CONDA_ENV
        
    def recommend(self, item: AuditItem) -> Recommendation:
        return Recommendation(
            title="Remove Conda Environment",
            explanation="Conda virtual environment.",
            safety_reason="Removing this environment will delete all installed packages within it.",
            rollback=RollbackStrategy.REQUIRES_MANUAL_RESTORE,
            rollback_notes="Must re-run `conda env create` to restore.",
            command=f"conda env remove -n {item.path.name}",
            files_affected=(item.path,),
            operation=CleanupOperation.DELETE_DIRECTORY
        )

class PythonInstallationRule(BaseRecommendationRule):
    def applies(self, item: AuditItem) -> bool:
        return item.category == Category.UNKNOWN and "Python" in item.description
        
    def recommend(self, item: AuditItem) -> Recommendation:
        version = item.metadata.get("version", "Unknown")
        is_duplicate = item.metadata.get("is_duplicate", False)
        primary = item.metadata.get("primary_path", "")
        
        title = "Remove duplicate Python installation" if is_duplicate else "Uninstall Python"
        explanation = f"Potential duplicate of Python {version} located at {primary}." if is_duplicate else f"Python {version} installation."
        
        return Recommendation(
            title=title,
            explanation=explanation,
            safety_reason="Removing a Python installation will break any scripts or virtual environments that depend on it.",
            rollback=RollbackStrategy.REQUIRES_MANUAL_RESTORE,
            rollback_notes="Must re-run the Python installer.",
            files_affected=(item.path,),
            operation=CleanupOperation.DELETE_DIRECTORY
        )

class ChromeAIModelRule(BaseRecommendationRule):
    def applies(self, item: AuditItem) -> bool:
        return item.category == Category.CHROME_AI_MODEL
        
    def recommend(self, item: AuditItem) -> Recommendation:
        return Recommendation(
            title="Delete Chrome AI Models",
            explanation="Chrome automatically downloads on-device AI models for features like Help Me Write.",
            safety_reason="Safe to delete. Chrome will re-download the models in the background if the features are used again.",
            operation=CleanupOperation.DELETE_DIRECTORY,
            rollback=RollbackStrategy.REGENERATES_AUTOMATICALLY,
            rollback_notes="Chrome automatically manages these.",
            files_affected=(item.path,)
        )

class ChromeCacheRule(BaseRecommendationRule):
    def applies(self, item: AuditItem) -> bool:
        return item.category == Category.BROWSER_CACHE
        
    def recommend(self, item: AuditItem) -> Recommendation:
        return Recommendation(
            title=f"Clear Chrome Cache",
            explanation="Temporary internet files stored by Chrome.",
            safety_reason="Safe to delete. Chrome will rebuild the cache as you browse.",
            operation=CleanupOperation.DELETE_DIRECTORY,
            rollback=RollbackStrategy.REGENERATES_AUTOMATICALLY,
            rollback_notes="Websites may load slightly slower the next time you visit them.",
            files_affected=(item.path,)
        )

class ChromeProfileRule(BaseRecommendationRule):
    def applies(self, item: AuditItem) -> bool:
        return item.category == Category.CHROME_PROFILE
        
    def recommend(self, item: AuditItem) -> Recommendation:
        return Recommendation(
            title="Delete Chrome Profile",
            explanation=f"User profile directory: {item.path.name}.",
            safety_reason="Deleting this will remove all browsing history, bookmarks, passwords, and extensions for this profile.",
            operation=CleanupOperation.DELETE_DIRECTORY,
            rollback=RollbackStrategy.NO_ROLLBACK_AVAILABLE,
            rollback_notes="Data cannot be recovered unless it was synced to a Google account.",
            files_affected=(item.path,)
        )

class DockerVolumeRule(BaseRecommendationRule):
    def applies(self, item: AuditItem) -> bool:
        return item.category == Category.PROJECT_DEPENDENCY and "Docker Volume" in item.description
        
    def recommend(self, item: AuditItem) -> Recommendation:
        vol_name = item.metadata.get("volume_name", item.path.name)
        return Recommendation(
            title=f"Review Docker Volume: {vol_name}",
            explanation="This is a Docker volume. It may contain database files or persistent state.",
            operation=CleanupOperation.DELETE_DIRECTORY,
            rollback=RollbackStrategy.REQUIRES_MANUAL_RESTORE,
            safety_reason="If this volume contains a database, deleting it will result in permanent data loss.",
            command=f"docker volume rm {vol_name}",
            files_affected=(item.path,)
        )

class DockerBuildCacheRule(BaseRecommendationRule):
    def applies(self, item: AuditItem) -> bool:
        return item.category == Category.BUILD_ARTIFACT and item.metadata.get("cache_type") == "buildkit"
        
    def recommend(self, item: AuditItem) -> Recommendation:
        return Recommendation(
            title="Clear Docker BuildKit Cache",
            explanation="Docker caches build layers here. They can be safely deleted to reclaim space.",
            operation=CleanupOperation.DELETE_DIRECTORY,
            rollback=RollbackStrategy.REGENERATES_AUTOMATICALLY,
            safety_reason="Build caches will automatically regenerate on the next docker build.",
            command="docker builder prune -a -f",
            files_affected=(item.path,)
        )

class SystemCacheRule(BaseRecommendationRule):
    def applies(self, item: AuditItem) -> bool:
        return item.category == Category.SYSTEM_CACHE
        
    def recommend(self, item: AuditItem) -> Recommendation:
        return Recommendation(
            title=f"Review System Cache",
            explanation="System-level virtual disk or cache storage.",
            operation=CleanupOperation.DELETE_DIRECTORY,
            rollback=RollbackStrategy.REQUIRES_MANUAL_RESTORE,
            safety_reason="Deleting this file will destroy the VM or backend.",
            files_affected=(item.path,)
        )

class DefaultRule(BaseRecommendationRule):
    def applies(self, item: AuditItem) -> bool:
        return True
        
    def recommend(self, item: AuditItem) -> Recommendation:
        return Recommendation(
            title=f"Review {item.path.name}",
            explanation=item.description,
            operation=CleanupOperation.DELETE_DIRECTORY if item.path.is_dir() else CleanupOperation.DELETE_FILE,
            rollback=RollbackStrategy.REQUIRES_MANUAL_RESTORE,
            safety_reason="Default operation.",
            files_affected=(item.path,)
        )

ALL_RULES = [
    PipCacheRule(),
    VirtualenvRule(),
    CondaRule(),
    PythonInstallationRule(),
    ChromeAIModelRule(),
    ChromeCacheRule(),
    ChromeProfileRule(),
    DockerVolumeRule(),
    DockerBuildCacheRule(),
    SystemCacheRule(),
]
