"""
Generate or update README.md from manifest.json.

Creates a complete README structure with shields, description, and installation instructions.
If README exists, updates shields and installation sections while preserving other content.

Usage:
  py generate_readme.py [directory]    # Generate/update README for directory (default: current)
"""

import json
import re
import sys
from pathlib import Path
from generate_shields import generate_shields
from generate_install_block import generate_installation_markdown


def create_new_readme(manifest: dict, package_dir: Path) -> str:
    """Create a new README from scratch."""
    title = manifest.get("title", manifest.get("name", "Talon Package"))
    description = manifest.get("description", "A Talon voice control package.")
    shields = generate_shields(manifest)
    installation = generate_installation_markdown(manifest)

    lines = [
        f"# {title}",
        "",
        *shields,
        "",
        description,
    ]

    # Add preview image if it exists
    if (package_dir / "preview.png").exists():
        lines.extend([
            "",
            '<img src="preview.png" alt="preview">',
        ])

    lines.extend([
        "",
        installation,
    ])

    return "\n".join(lines)


def update_existing_readme(content: str, manifest: dict, package_dir: Path) -> str:
    """Update shields in existing README, preserving all other content."""
    shields = generate_shields(manifest)
    installation = generate_installation_markdown(manifest)

    # Update or add shields at the top (after title)
    shield_pattern = r"!\[(Version|Status|Platform|Talon Beta)\]\([^\)]+\)"

    # Find first heading
    title_match = re.search(r"^#\s+.+$", content, re.MULTILINE)
    if title_match:
        title_end = title_match.end()
        # Look for existing shields after title
        after_title = content[title_end:]

        # Remove all existing shields
        after_title_cleaned = re.sub(shield_pattern + r"\s*", "", after_title)

        # Insert new shields after title
        shields_text = "\n\n" + "\n".join(shields)
        content = content[:title_end] + shields_text + after_title_cleaned
    else:
        # No title found, add shields at top
        shields_text = "\n".join(shields) + "\n\n"
        content = shields_text + content

    # Check if Installation/Install/Setup section exists
    install_section_pattern = r"^#{1,6}\s+.*\b(Installation|Install|Setup)\b"
    if not re.search(install_section_pattern, content, re.MULTILINE | re.IGNORECASE):
        # No installation section found, add it
        # Try to add before common sections like Usage, Features, License
        common_sections = re.search(r"^#{1,6}\s+(Usage|Features|License|Contributing|API)\s*$", content, re.MULTILINE | re.IGNORECASE)
        if common_sections:
            # Add before the first common section
            insert_pos = common_sections.start()
            content = content[:insert_pos] + installation + "\n\n" + content[insert_pos:]
        else:
            # No common sections, add at the end
            content = content.rstrip() + "\n\n" + installation + "\n"

    return content


def process_directory(package_dir: str):
    """Process a single directory."""
    package_dir = Path(package_dir).resolve()

    # Find manifest.json
    manifest_path = package_dir / "manifest.json"
    if not manifest_path.exists():
        print(f"❌ Error: manifest.json not found in {package_dir}")
        return False

    # Load manifest
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Check if README exists
    readme_path = package_dir / "README.md"

    try:
        if readme_path.exists():
            # Update existing README
            with open(readme_path, "r", encoding="utf-8") as f:
                content = f.read()

            updated_content = update_existing_readme(content, manifest, package_dir)

            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            print(f"✅ Updated {readme_path}")
        else:
            # Create new README
            new_content = create_new_readme(manifest, package_dir)

            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            print(f"✅ Created {readme_path}")
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
