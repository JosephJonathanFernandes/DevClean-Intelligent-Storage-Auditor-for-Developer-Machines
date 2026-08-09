from enum import Enum


class Category(Enum):
    """Represents the category of a discovered storage item."""
    
    PYTHON_CACHE = "python_cache"
    VENV = "venv"
    CONDA_ENV = "conda_env"
    
    NODE_CACHE = "node_cache"
    NODE_MODULES = "node_modules"
    NPM_CACHE = "npm_cache"
    PNPM_STORE = "pnpm_store"
    YARN_CACHE = "yarn_cache"
    
    DOCKER_IMAGE = "docker_image"
    DOCKER_VOLUME = "docker_volume"
    DOCKER_CONTAINER = "docker_container"
    
    BROWSER_CACHE = "browser_cache"
    CHROME_PROFILE = "chrome_profile"
    CHROME_AI_MODEL = "chrome_ai_model"
    PLAYWRIGHT = "playwright"
    
    WSL_DISTRO = "wsl_distro"
    
    UNKNOWN = "unknown"
