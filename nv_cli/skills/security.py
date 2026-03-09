"""Security scanner for skills."""

import re
from pathlib import Path
from typing import List, Tuple


class SecurityScanner:
    """Scans skill code for security issues."""

    DANGEROUS_PATTERNS = [
        # Execution
        (r'eval\s*\(', "Use of eval()"),
        (r'exec\s*\(', "Use of exec()"),
        (r'subprocess\.call\s*\([^)]*shell\s*=\s*True', "Shell execution with shell=True"),
        (r'os\.system\s*\(', "Use of os.system()"),
        # Imports
        (r'import\s+subprocess', "Imports subprocess"),
        (r'from\s+subprocess\s+import', "Imports from subprocess"),
        # File operations
        (r'open\s*\([^,)]*[,)]', "File operations"),
        # Network
        (r'import\s+socket', "Socket operations"),
        # Requests (may be okay for some skills)
        (r'import\s+requests', "Network requests"),
    ]

    CRITICAL_PATTERNS = [
        (r'__import__\s*\(', "Dynamic import"),
        (r'compile\s*\(', "Code compilation"),
        (r'import\s+ctypes', "Low-level operations"),
    ]

    def scan_file(self, filepath: Path) -> Tuple[List[str], List[str]]:
        """Scan a file for security issues.

        Returns: (warnings, critical)
        """
        try:
            content = filepath.read_text()
        except Exception as e:
            return [f"Error reading file: {e}"], []

        warnings = []
        critical = []

        for pattern, description in self.DANGEROUS_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                warnings.append(f"{description} in {filepath.name}")

        for pattern, description in self.CRITICAL_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                critical.append(f"{description} in {filepath.name}")

        return warnings, critical

    def scan_directory(self, dirpath: Path) -> Tuple[List[str], List[str]]:
        """Scan all Python files in directory."""
        all_warnings = []
        all_critical = []

        for filepath in dirpath.rglob("*.py"):
            warnings, critical = self.scan_file(filepath)
            all_warnings.extend(warnings)
            all_critical.extend(critical)

        return all_warnings, all_critical