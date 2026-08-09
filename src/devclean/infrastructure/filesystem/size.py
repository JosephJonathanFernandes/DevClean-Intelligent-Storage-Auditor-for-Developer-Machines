from pathlib import Path
from typing import Callable

def calculate_directory_size(path: Path, is_cancelled: Callable[[], bool]) -> int:
    """
    Safely calculates the total size of a directory in bytes.
    - Prevents symlink loops by not following symlinks by default.
    - Gracefully handles permission errors (skips inaccessible files).
    - Checks for cancellation during long traversals.
    """
    total_size = 0
    
    if not path.exists():
        return total_size

    # Avoid recursive os.walk if we want better symlink control and memory footprint
    # We use a stack for an iterative DFS traversal
    stack = [path]

    while stack:
        if is_cancelled():
            break
            
        current_dir = stack.pop()
        
        try:
            for item in current_dir.iterdir():
                if is_cancelled():
                    break
                    
                try:
                    # Do not follow symlinks
                    if item.is_symlink():
                        continue
                        
                    if item.is_dir():
                        stack.append(item)
                    elif item.is_file():
                        total_size += item.stat(follow_symlinks=False).st_size
                except (PermissionError, FileNotFoundError):
                    # File might have been deleted mid-scan, or we don't have access
                    continue
        except (PermissionError, FileNotFoundError):
            # Can't read this directory contents
            continue

    return total_size
