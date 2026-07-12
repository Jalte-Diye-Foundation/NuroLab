import os
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Union

def export_features(
    feature_vectors: List[List[Union[int, float]]],
    feature_names: List[str],
    metadata: Dict[str, Any],
    output_dir: str = None,
    filename_prefix: str = None
) -> tuple[str, str]:
    """
    Exports extracted EEG feature vectors into a clean CSV dataset format 
    alongside a JSON metadata file for downstream ML experiments.
    
    Parameters:
    -----------
    feature_vectors : List[List[float/int]]
        A 2D list/array where each inner list represents a single window's features.
    feature_names : List[str]
        A list of human-readable column names (e.g., matching the output from build_feature_names()).
    metadata : Dict[str, Any]
        A dictionary containing dataset parameters like sampling_rate, window_size, stride, etc.
    output_dir : str
        The directory path where files should be exported.
    filename_prefix : str, optional
        A custom prefix for the export files. If None, uses a timestamp.
        
    Returns:
    --------
    tuple[str, str]
        The absolute or relative file paths to the exported (csv_path, json_path).
    """

    
    # 1. Resolve output directory dynamically if not provided
    if output_dir is None:
        # __file__ is nurolab/processing/feature_exporter.py
        # .parent is nurolab/processing/
        # .parent.parent is nurolab/
        package_root = Path(__file__).resolve().parent.parent
        resolved_dir = package_root / "data" / "exports"
    else:
        resolved_dir = Path(output_dir)

    # Ensure the export directory exists
    os.makedirs(resolved_dir, exist_ok=True)
    
    
    # 2. Generate a unique timestamp string
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create unique filenames even if a standard prefix is passed from main.py
    if filename_prefix:
        csv_filename = f"{filename_prefix}_{timestamp_str}.csv"
        json_filename = f"{filename_prefix}_{timestamp_str}.json"
    else:
        csv_filename = f"eeg_features_{timestamp_str}.csv"
        json_filename = f"eeg_features_{timestamp_str}.json"
    
    csv_path = os.path.join(resolved_dir, csv_filename)
    json_path = os.path.join(resolved_dir, json_filename)
    
    # 3. Export the CSV File (Each row = one window, each column = one feature)
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        
        # Write human-readable headers (e.g., Fp1_alpha_DE, Fp1_beta_PSD)
        writer.writerow(feature_names)
        
        # Write feature rows
        for row in feature_vectors:
            writer.writerow(row)
            
    # 4. Include expected keys into the JSON metadata and merge user metadata
    full_metadata = {
        "export_timestamp": datetime.now().isoformat(),
        "total_windows": len(feature_vectors),
        "total_features": len(feature_names),
        "feature_names": feature_names,
        **metadata  # This unpacks sampling_rate, window_size, stride, channel_names, etc.
    }
    
    # 5. Export the JSON Metadata File
    with open(json_path, mode='w', encoding='utf-8') as json_file:
        json.dump(full_metadata, json_file, indent=4)
        
    print(f"Successfully exported dataset:")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}")
    
    return str(csv_path), str(json_path)
