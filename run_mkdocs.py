import pathlib
import site
import sys

import mkdocs.utils as mu

_original_get_theme_dir = mu.get_theme_dir


def _material_templates_dir() -> str:
    roots: list[pathlib.Path] = []
    for p in site.getsitepackages():
        roots.append(pathlib.Path(p))
    if getattr(sys, "prefix", None):
        roots.append(pathlib.Path(sys.prefix) / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages")
    seen: set[pathlib.Path] = set()
    for base in roots:
        if not base or base in seen:
            continue
        seen.add(base)
        candidate = base / "material" / "templates" / "mkdocs_theme.yml"
        if candidate.is_file():
            return str(candidate.parent.resolve())
    raise RuntimeError(
        "mkdocs-material: diretório de templates não encontrado (instale dependências com uv sync)"
    )


def _patch_material_theme_dir() -> None:
    def get_theme_dir(name: str) -> str:
        if name == "material":
            return _material_templates_dir()
        return _original_get_theme_dir(name)

    mu.get_theme_dir = get_theme_dir


def main() -> None:
    _patch_material_theme_dir()
    from mkdocs.__main__ import cli

    raise SystemExit(cli())


if __name__ == "__main__":
    main()
