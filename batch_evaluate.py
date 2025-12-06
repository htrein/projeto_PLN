import os
import glob
import subprocess

# --- CONFIGURATION ---
# Path to your gold file (correct answers)
GOLD_FILE = 'gold.txt' 

# Folder containing your model prediction files (e.g., gemma3_0shot.txt, etc.)
INPUT_FOLDER = 'runs/runs_regex' 

# Folder where the evaluation results will be saved
OUTPUT_FOLDER = 'runs/evaluations' 

# Path to the Spider database folder
DB_DIR = 'spider_data/database' 

# Path to the tables.json file
TABLE_FILE = 'spider_data/tables.json' 

# Evaluation type: 'match', 'exec', or 'all'
ETYPE = 'all' 
# ---------------------

def main():
    # 1. Create output directory if it doesn't exist
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"Created output directory: {OUTPUT_FOLDER}")

    if os.path.isfile(INPUT_FOLDER):
        # Case A: Input is a specific file
        prediction_files = [INPUT_FOLDER]
    elif os.path.isdir(INPUT_FOLDER):
        # Case B: Input is a folder, find all .txt files inside
        prediction_files = glob.glob(os.path.join(INPUT_FOLDER, '*.txt'))
    else:
        print(f"Error: Path '{INPUT_FOLDER}' does not exist.")
        return

    if not prediction_files:
        print(f"No .txt files found in {INPUT_FOLDER}")
        return

    print(f"Found {len(prediction_files)} files to evaluate.\n")

    # 3. Loop through each file and run evaluation
    for pred_file_path in prediction_files:
        # Get just the filename (e.g., "gemma3_0shot.txt")
        filename = os.path.basename(pred_file_path)
        
        # Define where to save the result
        output_file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        print(f"Processing: {filename}...")

        # Construct the command to run evaluation.py
        # We use the same arguments you used previously
        command = [
            "python3", "evaluation.py",
            "--gold", GOLD_FILE,
            "--pred", pred_file_path,
            "--db", DB_DIR,
            "--table", TABLE_FILE,
            "--etype", ETYPE
        ]

        try:
            # Run the command and capture stdout/stderr
            with open(output_file_path, "w") as outfile:
                # subprocess.run executes the command and pipes output to the file
                result = subprocess.run(
                    command, 
                    stdout=outfile, 
                    stderr=subprocess.STDOUT, # Capture errors in the same file
                    text=True
                )
                
            if result.returncode == 0:
                print(f"  ✅ Success! Output saved to: {output_file_path}")
            else:
                print(f"  ⚠️  Warning: evaluation.py returned an error code for {filename}. Check output file.")

        except Exception as e:
            print(f"  ❌ Error running evaluation for {filename}: {e}")

    print("\nBatch evaluation complete.")

if __name__ == "__main__":
    main()