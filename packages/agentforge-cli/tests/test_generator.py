from pathlib import Path

import pytest

from __PACKAGE_NAME__.generator import generate_project


def test_generate_project_creates_required_files(tmp_path: Path) -> None:
    project_dir = generate_project("claims-assistant", tmp_path)

    assert (project_dir / "pyproject.toml").is_file()
    assert (project_dir / ".env").is_file()
    assert (
        project_dir / "src" / "claims_assistant" / "__init__.py"
    ).is_file()
    assert (
        project_dir / "src" / "claims_assistant" / "main.py"
    ).is_file()
    assert (project_dir / "tests" / "test_smoke.py").is_file()


def test_generate_project_rejects_existing_directory(
    tmp_path: Path,
) -> None:
    (tmp_path / "claims-assistant").mkdir()

    with pytest.raises(FileExistsError):
        generate_project("claims-assistant", tmp_path)


def test_generate_project_creates_valid_python_package(
    tmp_path: Path,
) -> None:
    project_dir = generate_project("claims-assistant", tmp_path)

    assert (
        project_dir / "src" / "claims_assistant" / "services" / "greeter.py"
    ).is_file()