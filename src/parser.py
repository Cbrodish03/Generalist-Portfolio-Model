import os
import pandas as pd
import time

"""
A parser built for the Generalist-Portfolio-Model
Currently supports files of type: .xlsx
"""
class SIPParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.investments = self.validate_file_type()

    def validate_file_type(self):
        """
        Checks the file extension of the given file
        """
        filename, ext = os.path.splitext(self.filepath)
        if ext.lower() == '.xlsx':
            return self.parse_xlsx()
        else:
            raise ValueError(f"Invalid file type: {self.filepath}. Expected .xlsx (Excel) type")
        
    def parse_xlsx(self):
        """
        Parses the given Excel file and extracts relevant data
        """
        # start = time.time()
        # df = pd.read_excel(self.filepath, engine='openpyxl')    # takes roughly 3.7 seconds
        # print(f"Reading with openpyxl took {time.time() - start: .2f} seconds")

        # start = time.time()
        df = pd.read_excel(self.filepath, engine='calamine')    # new engine takes about 0.4 seconds
        # print(f"Reading with calamine took {time.time() - start: .2f} seconds")

        print(f"Data from {self.filepath}:\n")
        print(df.head(15))  # Display the first few rows of the data

        # Step 1: Find "Meta Data"
        meta_row, meta_col = None, None
        for r in range(df.shape[0]):
            for c in range(df.shape[1]):
                val = df.iat[r, c]
                if isinstance(val, str) and val.strip().lower() == "meta data":
                    meta_row, meta_col = r, c
                    # print(f"'Meta Data' found at row {r}, column {c}")
                    break
            if meta_col is not None:
                break

        if meta_col is None:
            print("No 'Meta Data' marker found in the file.")
            return []

        # Step 2: Collect metadata fields below the marker until an empty cell
        metadata_fields = []
        metadata_end = None
        for r in range(meta_row + 1, df.shape[0]):
            val = df.iat[r, meta_col]
            if pd.isna(val) or str(val).strip() == "":
                metadata_end = r
                break
            metadata_fields.append(str(val).strip())

        if not metadata_fields:
            raise ValueError("No metadata fields found under 'Meta Data' marker.")
        if metadata_end is None:
            raise ValueError("No empty row found after metadata fields.")

        print("Metadata fields:", metadata_fields)

        # Step 3: Scan column 1 for first trial index "1"
        trial_start = None
        for r in range(meta_row, df.shape[0]):
            val = df.iat[r, 1]
            if str(val).strip() == "1":
                trial_start = r
                # print(f"First trial found at row {r}, column 1")
                break

        if trial_start is None:
            raise ValueError("Could not find first trial index (1) in column 1.")

        # Step 4: Determine number of trials by scanning col 1 until NaN
        trial_indices = df.iloc[trial_start:, 1].dropna().astype(str)
        trial_count = 0
        for v in trial_indices:
            if v.isnumeric():
                trial_count += 1
            else:
                break

        print(f"Detected {trial_count} trials")

        # Step 5: Parse each investment column (col ≥ 2)
        group_data = []
        col_num = 0
        for col in df.columns[2:]:
            column_data = df[col].tolist()

            # Trials: trial_count rows starting at trial_start, force type coercion
            """
            Why force type coercion?
            without type coercion: ~18.5 seconds for 250 portfolios
            WITH type coercion: ~12.5 seconds for 250 portfolios
                                ~24.5 seconds for 500 portfolios
            """
            trials = pd.to_numeric(
                column_data[trial_start:trial_start + trial_count],
                errors="coerce"
            ).tolist()


            # Metadata: immediately after trials
            metadata_values = column_data[trial_start + trial_count: trial_start + trial_count + len(metadata_fields)]
            metadata = dict(zip(metadata_fields, metadata_values))

            group_entry = {
                "group_index": col_num,
                "metadata": metadata,
                "trials": trials
            }
            col_num+=1
            group_data.append(group_entry)

        print(f"Parsed {len(group_data)} groups")
        return group_data


def test_parser():
    # create test case to test the parser functionality
    test_parser = SIPParser("data/mock_sipmath_v2.xlsx")
    for g in test_parser.investments[:2]:
        print("Group:", g["group_index"])
        print("Metadata:", g["metadata"])
        print("First 5 trials:", g["trials"][:5])
        print("---")


# main method to test current state of parser
if __name__ == "__main__":
    test_parser()

