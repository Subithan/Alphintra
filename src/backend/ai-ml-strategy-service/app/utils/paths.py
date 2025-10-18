import os


def sanitize_relative_path(path: str) -> str:
    path = path.strip().replace("\\", "/")
    # Remove leading slashes
    while path.startswith("/"):
        path = path[1:]
    normalized = os.path.normpath(path)
    if normalized.startswith("..") or os.path.isabs(normalized):
        raise ValueError("Invalid file path")
    return normalized.replace("\\", "/")


def detect_language(filename: str) -> str:
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    mapping = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
        "jsx": "javascript",
        "html": "html",
        "css": "css",
        "json": "json",
        "md": "markdown",
        "sql": "sql",
        "yaml": "yaml",
        "yml": "yaml",
        "txt": "plaintext",
    }
    return mapping.get(ext, "plaintext")
