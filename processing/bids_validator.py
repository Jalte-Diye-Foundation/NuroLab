# File: nurolab/processing/bids_validator.py
# BIDS Dataset Validator
# Checks if an EEG dataset folder follows the Brain Imaging Data Structure
# standard before processing. Prevents cryptic errors later in the pipeline.
#
# BIDS standard reference: https://bids-specification.readthedocs.io

import json
from pathlib import Path


def validate_bids_dataset(dataset_root: str) -> dict:
    """
    Validates a BIDS EEG dataset folder structure.

    Checks for:
    - participants.tsv (required — subject metadata)
    - dataset_description.json (required — dataset info)
    - At least one subject folder (sub-XXX)
    - At least one EEG file per subject

    Args:
        dataset_root: path to the BIDS dataset root folder

    Returns:
        dict with validation results and any issues found
    """
    root = Path(dataset_root)
    issues   = []
    warnings = []
    passed   = []

    print(f"\nValidating BIDS dataset: {root}")
    print("=" * 60)

    # Check root exists
    if not root.exists():
        return {
            "valid":    False,
            "issues":   [f"Dataset folder not found: {root}"],
            "warnings": [],
            "passed":   [],
        }

    # Check participants.tsv
    participants = root / "participants.tsv"
    if participants.exists():
        passed.append("participants.tsv found")
        # Check it has required columns
        with open(participants) as f:
            header = f.readline().strip().split("\t")
        if "participant_id" not in header:
            issues.append("participants.tsv missing 'participant_id' column")
        else:
            passed.append("participants.tsv has 'participant_id' column")
        if "age" not in header:
            warnings.append("participants.tsv missing 'age' column (recommended)")
        if "sex" not in header:
            warnings.append("participants.tsv missing 'sex' column (recommended)")
    else:
        issues.append("participants.tsv not found (required)")

    # Check dataset_description.json
    description = root / "dataset_description.json"
    if description.exists():
        passed.append("dataset_description.json found")
        with open(description) as f:
            desc = json.load(f)
        if "Name" not in desc:
            warnings.append("dataset_description.json missing 'Name' field")
        if "BIDSVersion" not in desc:
            warnings.append("dataset_description.json missing 'BIDSVersion' field")
    else:
        warnings.append("dataset_description.json not found (recommended)")

    # Check subject folders
    subject_folders = sorted([
        d for d in root.iterdir()
        if d.is_dir() and d.name.startswith("sub-")
    ])

    if not subject_folders:
        issues.append("No subject folders found (expected sub-XXX folders)")
    else:
        passed.append(f"Found {len(subject_folders)} subject folder(s)")

        # Check each subject has an eeg folder with files
        subjects_with_eeg = 0
        subjects_missing_eeg = []

        for sub in subject_folders:
            eeg_folder = sub / "eeg"
            if eeg_folder.exists():
                eeg_files = list(eeg_folder.glob("*.set")) + \
                            list(eeg_folder.glob("*.bdf")) + \
                            list(eeg_folder.glob("*.edf"))
                if eeg_files:
                    subjects_with_eeg += 1
                else:
                    subjects_missing_eeg.append(sub.name)
            else:
                subjects_missing_eeg.append(sub.name)

        if subjects_with_eeg == 0:
            issues.append("No EEG files found in any subject folder")
        else:
            passed.append(f"{subjects_with_eeg} subject(s) have EEG files")

        if subjects_missing_eeg:
            warnings.append(
                f"These subjects have no EEG files: {subjects_missing_eeg}"
            )

    # Print results
    print(f"\n✓ Passed ({len(passed)}):")
    for p in passed:
        print(f"   ✓ {p}")

    if warnings:
        print(f"\n⚠️ Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"   ⚠️ {w}")

    if issues:
        print(f"\n✗ Issues ({len(issues)}):")
        for i in issues:
            print(f"   ✗ {i}")

    valid = len(issues) == 0
    print(f"\nResult: {'✓ Valid BIDS dataset' if valid else '✗ Invalid — fix issues above'}")

    return {
        "valid":    valid,
        "issues":   issues,
        "warnings": warnings,
        "passed":   passed,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python nurolab/processing/bids_validator.py <dataset_path>")
        print("Example: python nurolab/processing/bids_validator.py nurolab/data/ds003478")
        sys.exit(1)
    result = validate_bids_dataset(sys.argv[1])
    sys.exit(0 if result["valid"] else 1)