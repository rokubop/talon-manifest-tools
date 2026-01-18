"""
Run all generators in sequence: manifest, version, and readme.
Will update instead of overwriting existing code where relevant.

Usage:
  py generate_all.py [directory]    # Generate all files for directory (default: current)
"""

import sys
import subprocess
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()


def run_generator(script_name: str, directory: str) -> bool:
    """Run a generator script and return success status."""
    try:
        # Build full path to the generator script
        script_path = SCRIPT_DIR / script_name
        result = subprocess.run(
            [sys.executable, str(script_path), directory],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout, end='')
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running {script_name}:")
        print(e.stdout, end='')
        print(e.stderr, end='')
        return False


def process_directory(package_dir: Path) -> bool:
    """Process a single directory with all generators."""
    if not package_dir.exists():
        print(f"Error: Directory not found: {package_dir}")
        return False

    print(f"\nGenerating files for: {package_dir}")
    print("=" * 60)

    # Run generators in sequence
    generators = [
        "generate_manifest.py",
        "generate_version.py",
        "generate_readme.py"
    ]

    for generator in generators:
        print(f"\nRunning {generator}...")
        print("-" * 60)
        if not run_generator(generator, str(package_dir)):
            print(f"Failed at {generator}")
            return False

    print(f"All generators completed for {package_dir}")
    return True


def main():
    # Get directories from arguments or use current directory
    if len(sys.argv) > 1:
        package_dirs = [Path(d).resolve() for d in sys.argv[1:]]
    else:
        package_dirs = [Path(".").resolve()]

    success_count = 0
    total_count = len(package_dirs)

    for package_dir in package_dirs:
        if process_directory(package_dir):
            success_count += 1

    print("\n" + "=" * 60)
    if success_count == total_count:
        if total_count == 1:
            print("SUCCESS: All generators completed successfully!")
        else:
            print(f"SUCCESS: All {total_count} directories processed successfully!")
    else:
        print(f"Processed {success_count}/{total_count} directories successfully")


if __name__ == "__main__":
    main()
