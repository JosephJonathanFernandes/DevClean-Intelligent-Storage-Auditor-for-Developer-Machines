from enum import Enum

class RollbackStrategy(Enum):
    REGENERATES_AUTOMATICALLY = "regenerates_automatically"
    REQUIRES_REDOWNLOAD = "requires_redownload"
    REQUIRES_MANUAL_RESTORE = "requires_manual_restore"
    ARCHIVE_AND_RESTORE = "archive_and_restore"
    NO_ROLLBACK_AVAILABLE = "no_rollback_available"

class CleanupOperation(Enum):
    DELETE_DIRECTORY = "delete_directory"
    DELETE_FILE = "delete_file"
    PURGE_CACHE = "purge_cache"
    REMOVE_VOLUME = "remove_volume"
    ARCHIVE = "archive"

class CleanupMode(Enum):
    DRY_RUN = "dry_run"
    EXECUTE = "execute"
    VERIFY_ONLY = "verify_only"
