import os
import glob
import re


INPUT_FOLDER = "./runs/runs"   # Folder containing your raw model outputs
OUTPUT_FOLDER = "./runs/runs_regex" # Folder where cleaned files will be saved


def repair_and_extract_sql(text):

    # Remove leading/trailing whitespace
    text = text.strip()
    
    # 1. Clean up markdown wrappers if present (e.g., ```sql ... ```)
    # We keep IGNORECASE here because markdown tags can be `sql` or `SQL`
    match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        text = match.group(1)
        
    # 2. Strategy: Find the start of the SQL
    # STRICT CASE MATCHING: Removed re.IGNORECASE
    # This ensures we match "SELECT * FROM..." but ignore "I will select the best option..."
    select_match = re.search(r"\bSELECT\b", text)
    
    if select_match:
        # SQL starts here
        start_index = select_match.start()
        sql = text[start_index:]
    else:
        # 3. Fallback: "Missing SELECT" Pattern
        # STRICT CASE MATCHING: Removed re.IGNORECASE
        # We only treat it as a query if it contains an uppercase "FROM"
        # This avoids matching: "The data comes from the server."
        from_match = re.search(r"\bFROM\b", text)
        if from_match:
            # Prepend SELECT and treat the whole string as the query
            sql = "SELECT " + text
        else:
            # If there's no SELECT and no FROM, it's likely conversational garbage.
            return text

    # 4. Strategy: Find the end of the SQL (The Semicolon)
    if ";" in sql:
        sql = sql.split(";")[0] + ";"
    
    # 5. Final Cleanup (Remove trailing conversational text if no semicolon was found)
    # Models often output: "SELECT * FROM table\nThis query will..."
    if "\n" in sql:
        lines = sql.split("\n")
        clean_lines = []
        for line in lines:
            # Heuristic: Stop if we hit a common explanation pattern start
            if re.match(r"^(This|Note|Here|The|In this|To answer)", line.strip(), re.IGNORECASE):
                break
            clean_lines.append(line)
        sql = " ".join(clean_lines)

    # Collapse multiple spaces into one
    sql = re.sub(r'\s+', ' ', sql).strip()
    
    return sql

# ==========================================
# 3. File Processing Logic
# ==========================================
def process_folder(input_dir, output_dir):
    # 1. Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

    # 2. Determine if the input is a single file or a directory
    if os.path.isfile(input_dir):
        # Case A: Input is a specific file
        prediction_files = [input_dir]
    elif os.path.isdir(input_dir):
        # Case B: Input is a folder, find all .txt files inside
        prediction_files = glob.glob(os.path.join(input_dir, '*.txt'))
    else:
        print(f"Error: Path '{input_dir}' does not exist.")
        return

    if not prediction_files:
        print(f"No files found to process in {input_dir}")
        return

    print(f"Found {len(prediction_files)} files. Processing...")

    for file_path in prediction_files:
        filename = os.path.basename(file_path)
        output_path = os.path.join(output_dir, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as infile, \
                 open(output_path, 'w', encoding='utf-8') as outfile:
                
                line_count = 0
                for line in infile:
                    cleaned_sql = repair_and_extract_sql(line)
                    outfile.write(cleaned_sql + '\n')
                    line_count += 1
            
            print(f"Processed: {filename} ({line_count} lines)")
            
        except Exception as e:
            print(f"Failed to process {filename}: {e}")

    print("Done.")

# ==========================================
# 4. Main Execution
# ==========================================
if __name__ == "__main__":
    process_folder(INPUT_FOLDER, OUTPUT_FOLDER)
