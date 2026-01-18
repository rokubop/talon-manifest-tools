"""
Generate shield badges from manifest.json.

e.g., version, status, platform (optional), requiresTalonBeta (only if true).
(version | 1.0.0)
(status | stable)
(platform | windows | mac | linux)
(talon beta | required)

Usage:
  py generate_shields.py [directory]    # Generate shields for directory (default: current)
                                         # If shields exist in README, updates them
                                         # If not, prints a display block to copy
"""

import json
import re
import sys
from pathlib import Path

STATUS_COLORS = {
    "stable": "green",
    "preview": "orange",
    "experimental": "orange",
    "prototype": "red",
    "reference": "blue",
    "deprecated": "red",
    "archived": "lightgrey"
}

def generate_shields(manifest: dict) -> list[str]:
    """Generate shield badge markdown lines from manifest data."""
    shields = []

    # Version badge
    version = manifest.get("version", "0.0.0")
    shields.append(f"![Version](https://img.shields.io/badge/version-{version}-blue)")

    # Status badge with color
    status = manifest.get("status", "unknown").lower()
    status_color = STATUS_COLORS.get(status, "lightgrey")
    shields.append(f"![Status](https://img.shields.io/badge/status-{status}-{status_color})")

    # Platform badge (optional)
    platforms = manifest.get("platforms")
    if platforms:
        platform_str = "%20%7C%20".join(platforms)  # " | " encoded
        shields.append(f"![Platform](https://img.shields.io/badge/platform-{platform_str}-lightgrey)")

    # Requires Talon Beta badge (if true)
    if manifest.get("requires_talon_beta") or manifest.get("requiresTalonBeta"):
        shields.append("![Talon Beta](https://img.shields.io/badge/talon%20beta-required-red)")

    return shields


def update_readme(readme_path: Path, manifest: dict) -> bool:
    """Update README.md shields. Returns True if updated."""
    if not readme_path.exists():
        return False

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content
    updated = False

    # Update version shield
    version = manifest.get("version", "0.0.0")
    version_pattern = r"!\[Version\]\(https://img\.shields\.io/badge/version-[^\)]+\)"
    version_shield = f"![Version](https://img.shields.io/badge/version-{version}-blue)"
    if re.search(version_pattern, content):
        content = re.sub(version_pattern, version_shield, content)
        updated = True

    # Update status shield
    status = manifest.get("status", "unknown").lower()
    status_color = STATUS_COLORS.get(status, "lightgrey")
    status_pattern = r"!\[Status\]\(https://img\.shields\.io/badge/status-[^\)]+\)"
    status_shield = f"![Status](https://img.shields.io/badge/status-{status}-{status_color})"
    if re.search(status_pattern, content):
        content = re.sub(status_pattern, status_shield, content)
        updated = True

    # Update or add platform shield
    platforms = manifest.get("platforms")
    platform_pattern = r"!\[Platform\]\(https://img\.shields\.io/badge/platform-[^\)]+\)"
    if platforms:
        platform_str = "%20%7C%20".join(platforms)
        platform_shield = f"![Platform](https://img.shields.io/badge/platform-{platform_str}-lightgrey)"
        if re.search(platform_pattern, content):
            content = re.sub(platform_pattern, platform_shield, content)
            updated = True
        elif re.search(status_pattern, original_content):
            # Add platform shield after status if it doesn't exist
            content = re.sub(status_pattern, f"{status_shield}\n{platform_shield}", content)
            updated = True

    # Update, add, or remove Talon Beta shield
    beta_pattern = r"!\[Talon Beta\]\(https://img\.shields\.io/badge/talon%20beta-[^\)]+\)"
    requires_beta = manifest.get("requires_talon_beta") or manifest.get("requiresTalonBeta")
    if requires_beta:
        beta_shield = "![Talon Beta](https://img.shields.io/badge/talon%20beta-required-red)"
        if re.search(beta_pattern, content):
            content = re.sub(beta_pattern, beta_shield, content)
            updated = True
        elif re.search(status_pattern, original_content):
            # Add beta shield after status/platform if it doesn't exist
            if platforms and re.search(platform_pattern, content):
                # Insert after platform
                content = re.sub(platform_pattern, f"{platform_shield}\n{beta_shield}", content)
            else:
                # Insert after status
                content = re.sub(status_pattern, f"{status_shield}\n{beta_shield}", content)
            updated = True
    else:
        # Remove beta shield if it exists but not required
        if re.search(beta_pattern, content):
            content = re.sub(beta_pattern + r"\n?", "", content)
            updated = True

    if updated:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True

    return False


def print_display_block(shields: list[str]):
    """Print shields in a display block format similar to generate_install_block."""
    print("\n" + "=" * 60)
    print("Shield Badges (copy to README.md)")
    print("=" * 60)
    for shield in shields:
        print(shield)
    print("=" * 60 + "\n")


def process_directory(package_dir: str):
    """Process a single directory."""
    package_dir = Path(package_dir).resolve()

    # Find manifest.json
    manifest_path = package_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"❌ Error: manifest.json not found in {package_dir}")
        return False

    # Load manifest
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        # Generate shields
        shields = generate_shields(manifest)

        # Check if README exists
        readme_path = package_dir / "README.md"

        if readme_path.exists():
            updated = update_readme(readme_path, manifest)
            if updated:
                print(f"✅ Updated shields in {readme_path}")
            else:
                # README exists but no shields found - print display block
                print(f"\nShields for {package_dir}:")
                print_display_block(shields)
        else:
            # No README - print display block
            print(f"\nShields for {package_dir}:")
            print_display_block(shields)
        return True
    except Exception as e:
        print(f"❌ Error processing {package_dir}: {e}")
        return False


def main():
    # Get directories from arguments or use current directory
    if len(sys.argv) > 1:
        package_dirs = sys.argv[1:]
    else:
        package_dirs = ["."]

    success_count = 0
    total_count = len(package_dirs)

    for package_dir in package_dirs:
        if process_directory(package_dir):
            success_count += 1

    if total_count > 1:
        print(f"\nProcessed {success_count}/{total_count} directories successfully")


if __name__ == "__main__":
    main()
