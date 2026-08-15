import os
import re

target_files = [
    r"src\devclean\infrastructure\chrome\detectors\ai_models.py",
    r"src\devclean\infrastructure\chrome\detectors\cache.py",
    r"src\devclean\infrastructure\chrome\detectors\profiles.py",
    r"src\devclean\infrastructure\docker\detectors.py",
    r"src\devclean\infrastructure\python\detectors\conda.py",
    r"src\devclean\infrastructure\python\detectors\installations.py",
    r"src\devclean\infrastructure\python\detectors\pip_cache.py",
    r"src\devclean\infrastructure\python\detectors\virtualenvs.py",
    r"src\devclean\infrastructure\wsl\detectors.py",
]

for path in target_files:
    if not os.path.exists(path):
        continue
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove import
    content = re.sub(r'from devclean\.domain\.entities\.recommendation import Recommendation\n?', '', content)
    
    # Remove rec = Recommendation(...)
    content = re.sub(r'[ \t]*rec\s*=\s*Recommendation\([^)]*\)\n', '', content)
    
    # In some places it spans multiple lines. Wait, a regex matching across lines might be tricky.
    # It's better to use regex with re.DOTALL, but carefully.
    content = re.sub(r'[ \t]*rec\s*=\s*Recommendation\([^)]*\)\n', '', content, flags=re.DOTALL)
    
    # Remove recommendation=rec, or recommendation=Recommendation(...)
    content = re.sub(r'[ \t]*recommendation=rec,\n?', '', content)
    content = re.sub(r'[ \t]*recommendation=Recommendation\([^)]*\),\n?', '', content, flags=re.DOTALL)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
