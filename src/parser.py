import os
import pandas as pd
import math

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
        df = pd.read_excel(self.filepath, header=None)
        # print(f"Data from {self.filepath}:\n")
        # print(excel_data.head(15))  # Display the first few rows of the data

        # Step 1: Identify where the actual trial data starts by skipping the first two empty rows
        # TODO: add logic to preserve the header row (if important)
        start_row = None

        for i, row in df.iterrows():
            if row[1] == 1:
                start_row = i
                break

        if start_row is None:
            raise ValueError("Could not find trial start indicator.")

        # Step 2: Truncate data to start from the identified row
        trial_df = df.iloc[start_row:]

        # Step 3: Collect trial info and metadata from the columns
        group_data = []
        metadata_fields = ['Name', 'ExpectedRevenue', 'BusinessUnit', 'ProductType']
        num_rows = trial_df.shape[0]
        trial_end_row = num_rows - 4

        for col in trial_df.columns[2:]:
            column_data = trial_df[col].tolist()
            trials = column_data[:trial_end_row]
            metadata_values = column_data[trial_end_row:]

            group_entry = {
                "group_index": col - 2,
                "metadata": dict(zip(metadata_fields, metadata_values)),
                "trials": trials
            }

            group_data.append(group_entry)

        # print(group_data)
        return group_data


def test_validation():
    # create test case pairs of {filepath, bool}
    # where filepath is the name of the file, bool is whether it should be expected or not
    test_cases = {
        "valid_file.xlsx" : True,
        "capitalized_file.XLSX" : True,
        "noExtensionFile" : False, 
        "wrong_extension.xls" : False,
        "invalid_file.txt" : False
    }

    print("Running Parser file validity check:\n")
    for filepath, expected in test_cases.items():
        try:
            parser = SIPParser(filepath)
            print(f"{filepath}: passed")
            if not expected:
                print(f"{filepath}: expected failure but passed")
        except ValueError as e:
            print(f"{filepath}: {e}")
            if expected:
                print(f"{filepath}: expected pass but failed")

def test_parser():
    # create test case to test the parser functionality
    test_parser = SIPParser("data/small_SIP.xlsx")



# main method to test current state of parser
if __name__ == "__main__":
    # test_validation()
    test_parser()

