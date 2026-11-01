import os
import csv
import glob

# Define directories and CSV file path
rcsb_dir = '/net/scratch/pkwon2/repeats_rcsb'
alphafold_dir = '/net/scratch/pkwon2/repeats_alphafold'
csv_file = '/home/pkwon2/STRPsearch/merged.csv'

# Checkpoint file to record processed pdbs
checkpoint_file = 'processed_checkpoints.txt'

def load_checkpoint(checkpoint_path):
    """Load the set of processed pdb file paths from the checkpoint file."""
    processed = set()
    if os.path.exists(checkpoint_path):
        with open(checkpoint_path, 'r') as cf:
            for line in cf:
                processed.add(line.strip())
    return processed

def update_checkpoint(checkpoint_path, pdb_path):
    """Append the processed pdb file path to the checkpoint file."""
    with open(checkpoint_path, 'a') as cf:
        cf.write(pdb_path + "\n")

def process_pdb(pdb_file, start, end, search_dir):
    """Process a pdb file:
       - For ATOM records, keep only atoms whose residue number is within [start, end].
       - For HETATM records in RCSB pdb files, remove all heteroatoms.
       - For HETATM records in other pdb files, keep them unaltered.
       - Other lines (e.g. TER, END) remain unaltered.
    """
    try:
        with open(pdb_file, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Failed to open {pdb_file}: {e}")
        return False

    new_lines = []
    for line in lines:
        if line.startswith("ATOM"):
            # Residue number is typically in columns 23-26 (0-indexed 22:26)
            try:
                resnum_str = line[22:26].strip()
                resnum = int(resnum_str)
            except ValueError:
                # In case of any conversion issues, keep the line unmodified.
                new_lines.append(line)
                continue

            # Keep only atoms in the desired residue range.
            if start <= resnum <= end:
                new_lines.append(line)
            else:
                # Skip atoms outside of the range.
                continue
        elif line.startswith("HETATM"):
            if search_dir == rcsb_dir:
                # Remove all HETATM lines for RCSB pdb files.
                continue
            else:
                # For Alphafold pdbs or other sources, keep heteroatom records.
                new_lines.append(line)
        else:
            # For other lines (TER, END, etc.) simply keep them.
            new_lines.append(line)

    try:
        # Write the processed content back to the same file.
        with open(pdb_file, 'w') as f:
            f.writelines(new_lines)
        print(f"Processed: {pdb_file}")
        return True
    except Exception as e:
        print(f"Failed to write processed file {pdb_file}: {e}")
        return False

def main():
    processed_files = load_checkpoint(checkpoint_file)

    # Read the CSV
    with open(csv_file, newline='') as csvf:
        reader = csv.DictReader(csvf)
        for row in reader:
            try:
                start = int(row["start"])
                end = int(row["end"])
            except ValueError:
                print(f"Skipping row with invalid start/end values: {row}")
                continue

            source = row["source"].strip()
            structure = row["structure"].strip()

            # Determine which directory to search based on the source.
            if "RCSB" in source:
                search_dir = rcsb_dir
            elif "AlphaFold" in source:
                search_dir = alphafold_dir
            else:
                print(f"Unknown source '{source}' for structure '{structure}'. Skipping row.")
                continue

            # Glob for pdb files that match the structure pattern.
            pdb_pattern = os.path.join(search_dir, f"*{structure}*.pdb")
            pdb_files = glob.glob(pdb_pattern)

            if not pdb_files:
                print(f"No PDB files found for pattern: {pdb_pattern}")
                continue

            for pdb_file in pdb_files:
                # If already processed, skip this file.
                if pdb_file in processed_files:
                    print(f"Skipping already processed file: {pdb_file}")
                    continue

                # Process the pdb file
                if process_pdb(pdb_file, start, end, search_dir):
                    # Update the checkpoint upon successful processing.
                    update_checkpoint(checkpoint_file, pdb_file)
                    processed_files.add(pdb_file)

if __name__ == '__main__':
    main()