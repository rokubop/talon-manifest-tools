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

def create_new_readme(manifest: dict, package_dir: Path) -> str:
    """Create a new README from scratch."""
    from generate_shields import generate_shields, should_generate_shields
    from generate_install_block import generate_installation_markdown

    title = manifest.get("title", manifest.get("name", "Talon Package"))
    description = manifest.get("description", "A Talon voice control package.")
    status = manifest.get("status", "").lower()

    lines = [
        f"# {title}",
        "",
    ]

    # Add shields if enabled
    should_generate, _ = should_generate_shields(manifest)
    if should_generate:
        shields = generate_shields(manifest)
        lines.extend(shields)
        lines.append("")

    lines.append(description)

    # Add preview image if it exists
    if (package_dir / "preview.png").exists():
        lines.extend([
            "",
            '<img src="preview.png" alt="preview">',
        ])

    # Skip installation for reference, archived, or deprecated packages
    if status not in ["reference", "archived", "deprecated"]:
        installation = generate_installation_markdown(manifest)
        lines.extend([
            "",
            installation,
        ])

    return "\n".join(lines)


def update_existing_readme(content: str, manifest: dict, package_dir: Path) -> tuple[str, list[str]]:
    """Update shields in existing README, preserving all other content. Returns (content, actions_taken)."""
    from generate_shields import generate_shields, should_generate_shields
    from generate_install_block import generate_installation_markdown

    installation = generate_installation_markdown(manifest)
    status = manifest.get("status", "").lower()
    actions = []

    # Check if we should generate shields
    should_generate, _ = should_generate_shields(manifest)

    # Shield pattern to find existing shields
    shield_pattern = r"!\[(Version|Status|Platform|License|Talon Beta)\]\([^\)]+\)"

    # Check if shields already exist anywhere in the content
    existing_shields = re.findall(shield_pattern, content)

    if should_generate:
        shields = generate_shields(manifest)

    if existing_shields and should_generate:
        # Shields exist - update them in place
        # Replace each old shield with corresponding new shield
        shield_lines = "\n".join(shields)
        # Find all shields as a block (consecutive lines with optional blank lines between)
        shield_block_pattern = r"(?:" + shield_pattern + r"\s*)+"
        content = re.sub(shield_block_pattern, shield_lines + "\n\n", content, count=1)
        actions.append("updated shields")
    elif not existing_shields and should_generate:
        # No shields exist - add them
        # Try to add after title
        title_match = re.search(r"^#\s+.+$", content, re.MULTILINE)
        if title_match:
            title_end = title_match.end()
            shields_text = "\n\n" + "\n".join(shields) + "\n\n"
            content = content[:title_end] + shields_text + content[title_end:].lstrip()
            actions.append("added shields after title")
        else:
            # No title found, add at start
            shields_text = "\n".join(shields) + "\n\n"
            content = shields_text + content.lstrip()
            actions.append("added shields at start")
    elif not should_generate:
        actions.append("skipped shields (disabled)")

    # Check if Installation/Install/Setup section exists
    install_section_pattern = r"^#{1,6}\s+.*\b(Installation|Install|Setup)\b"

    # Only add installation section if status allows it and section doesn't exist
    if status not in ["reference", "archived", "deprecated"]:
        if not re.search(install_section_pattern, content, re.MULTILINE | re.IGNORECASE):
            # No installation section found, add it
            actions.append("added installation section")
            # Try to add before common sections like Usage, Features, License
            common_sections = re.search(r"^#{1,6}\s+(Usage|Features|License|Contributing|API)\s*$", content, re.MULTILINE | re.IGNORECASE)
            if common_sections:
                # Add before the first common section
                insert_pos = common_sections.start()
                content = content[:insert_pos] + installation + "\n\n" + content[insert_pos:]
            else:
                # No common sections, add at the end
                content = content.rstrip() + "\n\n" + installation + "\n"

    return content, actions


def process_directory(package_dir: str, dry_run: bool = False, verbose: bool = False, alt_manifest_path: str = None):
    """Process a single directory."""
    package_dir = Path(package_dir).resolve()

    # Find manifest.json (or use alternate path if provided)
    manifest_path = Path(alt_manifest_path) if alt_manifest_path else package_dir / "manifest.json"
    if not manifest_path.exists():
        if dry_run:
            from diff_utils import DIM, RESET
            print(f"README.md: {DIM}(skipped - manifest.json doesn't exist yet){RESET}")
            return True
        else:
            from diff_utils import RED, RESET
            print(f"{RED}Error: manifest.json not found in {package_dir}{RESET}")
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

            updated_content, actions = update_existing_readme(content, manifest, package_dir)

            if dry_run:
                # Show diff without writing
                from diff_utils import diff_text, format_diff_output, status_no_change, DIM, RESET

                has_changes, diff_output = diff_text(content, updated_content, "README.md")

                if has_changes:
                    print(f"README.md: {DIM}(dry run){RESET}")
                    print(format_diff_output(diff_output))
                else:
                    print(status_no_change("README.md"))
            else:
                # Compare and show diff or "no changes"
                from diff_utils import diff_text, format_diff_output, status_no_change, status_created

                has_changes, diff_output = diff_text(content, updated_content, "README.md")

                if has_changes:
                    with open(readme_path, "w", encoding="utf-8") as f:
                        f.write(updated_content)
                    print(f"README.md:")
                    print(format_diff_output(diff_output))
                else:
                    print(status_no_change("README.md"))
        else:
            # Create new README
            new_content = create_new_readme(manifest, package_dir)

            if dry_run:
                from diff_utils import diff_text, format_diff_output, status_created, DIM, RESET
                print(status_created("README.md") + f" {DIM}(dry run){RESET}")
                # Show full content as diff (all + lines)
                _, new_diff = diff_text("", new_content, "README.md")
                print(format_diff_output(new_diff))
            else:
                from diff_utils import diff_text, format_diff_output, status_created
                with open(readme_path, "w", encoding="utf-8") as f:
                    f.write(new_content)

                print(status_created("README.md"))
                # Show full content as diff (all + lines)
                _, new_diff = diff_text("", new_content, "README.md")
                print(format_diff_output(new_diff))
        return True
    except Exception as e:
        from diff_utils import RED, RESET
        print(f"{RED}Error processing {package_dir}: {e}{RESET}")
        return False


def main():
    # Parse flags
    dry_run = "--dry-run" in sys.argv
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    # Get alternate manifest path (for dry-run mode with mock manifest)
    alt_manifest_path = None
    skip_next = False
    package_dirs = []
    for i, arg in enumerate(sys.argv[1:], 1):
        if skip_next:
            skip_next = False
            continue
        if arg == "--manifest-path" and i + 1 < len(sys.argv):
            alt_manifest_path = sys.argv[i + 1]
            skip_next = True
        elif not arg.startswith('--'):
            package_dirs.append(arg)

    if not package_dirs:
        package_dirs = ["."]

    if dry_run and verbose:
        print("DRY RUN MODE - No files will be modified\n")

    success_count = 0
    total_count = len(package_dirs)

    for package_dir in package_dirs:
        if process_directory(package_dir, dry_run, verbose, alt_manifest_path):
            success_count += 1

    if total_count > 1 and verbose:
        print(f"\nProcessed {success_count}/{total_count} directories successfully")

if __name__ == "__main__":
    main()
