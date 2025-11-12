import os
import pandas as pd
import numpy as np
import time

"""
A parser built for the Generalist-Portfolio-Model
Currently supports files of type: .xlsx
"""
class SIPParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.investments = self.validate_file_type()

        self.wind_mappings = {}     # Mapping of wind name → {investment name: coefficient}
        self.wind_sip_values = {}   # Mapping of wind name → list of trial values

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

        # print(f"Data from {self.filepath}:\n")
        # print(df.head(15))  # Display the first few rows of the data

        # Quick detection for Winds of Fortune template files:
        basename = os.path.basename(self.filepath).lower()
        if "template" in basename.lower():
            # print("Detected Winds of Fortune template format, parsing as winds template.")
            return self.parse_winds_template(df)

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
            # print("No 'Meta Data' marker found in the file.")
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

        # print("Metadata fields:", metadata_fields)

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

        # print(f"Detected {trial_count} trials")

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
            # trials = pd.to_numeric(
            #     column_data[trial_start:trial_start + trial_count],
            #     errors="coerce"
            # ).tolist()

            trials = pd.Series(pd.to_numeric(
                column_data[trial_start:trial_start + trial_count],
                errors="coerce"
            ))

            # Skip columns that have no numeric data (all NaN)
            if trials.dropna().empty:
                continue

            # Keep NaNs in the trials list to preserve alignment/length
            trials = trials.tolist()

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

        # print(f"Parsed {len(group_data)} groups")
        return group_data

    def parse_winds_template(self, df):
        """
        Parse a Winds of Fortune template file
        Expected layout:
            Header row contains 'Investments' in first column, then wind names in following columns
            Rows below contain investment names in first column, then values for each wind in following columns
        :param df: the dataframe to parse
        :return: group entries where metadata contains:
            'InvestmentName': name of the investment
            'WindCoefficients': {wind_name: coefficient}
        """
        # find header row and header column (where cell equals 'Investment' / 'Investments' / 'Investment Name')
        header_row = None
        header_col = None
        for r in range(df.shape[0]):
            for c in range(df.shape[1]):
                val = df.iat[r, c]
                if isinstance(val, str) and val.strip().lower() in ("investment", "investments", "investment name"):
                    header_row = r
                    header_col = c
                    break
            if header_row is not None:
                break

        # fallback: use first non-empty cell in first row as header column if not found
        if header_row is None:
            header_row = 0
            for c in range(df.shape[1]):
                if not pd.isna(df.iat[header_row, c]) and str(df.iat[header_row, c]).strip() != "":
                    header_col = c
                    break
            if header_col is None:
                header_col = 0

        # prepare header names (full dataframe row)
        headers = df.iloc[header_row].tolist()
        header_names = []
        for h in headers:
            if pd.isna(h):
                header_names.append("")
            else:
                header_names.append(str(h).strip())

        # determine wind columns (those to the right of the investment column)
        wind_cols = []
        for c in range(header_col + 1, df.shape[1]):
            name = header_names[c] if c < len(header_names) else ""
            wind_cols.append((c, name if name else f"col_{c}"))

        group_data = []
        group_index = 0

        # parse rows below header_row until an empty investment name encountered
        for r in range(header_row + 1, df.shape[0]):
            inv_name_raw = df.iat[r, header_col]
            if pd.isna(inv_name_raw) or str(inv_name_raw).strip() == "":
                # stop at first empty investment name row
                break
            investment_name = str(inv_name_raw).strip()

            winds_dict = {}
            for cidx, wind_name in wind_cols:
                val = df.iat[r, cidx]
                coeff = pd.to_numeric(val, errors="coerce")
                if pd.isna(coeff):
                    coeff = 0.0
                else:
                    coeff = float(coeff)
                winds_dict[wind_name] = coeff

            metadata = {
                "Name": investment_name,
                "WindCoefficients": winds_dict
            }

            group_entry = {
                "group_index": group_index,
                "metadata": metadata,
            }
            group_data.append(group_entry)
            group_index += 1

        # print(f"Parsed {len(group_data)} winds-template groups")
        return group_data

    def apply_winds(self, simulated_groups, template_groups, wind_groups):
        """
        Apply Winds of Fortune adjustments:
            updated_trial[t] = original_trial[t] + (relationship_pct * wind_sip_value[t])
        :param simulated_groups: the investment groups to adjust
        :param template_groups: the winds template groups defining relationships
        :param wind_groups: the wind SIP groups defining wind trial values
        :return: adjusted investment groups
        """
        # break down the wind template into wind type --> investment name, coefficient
        wind_mappings = {}  # wind_name -> { investment_name: coefficient }
        for tg in template_groups:
            inv_name = tg["metadata"].get("Name", "")
            wind_coeffs = tg["metadata"].get("WindCoefficients", {})
            for wind_name, coeff in wind_coeffs.items():
                if wind_name not in wind_mappings:
                    wind_mappings[wind_name] = {}
                wind_mappings[wind_name][inv_name] = coeff
        # print("Wind mappings:", wind_mappings)
        self.wind_mappings = wind_mappings
        # break down the wind SIP into wind type --> trial values
        wind_sip_values = {}  # wind_name -> [trial values]
        for wg in wind_groups:
            wind_name = wg["metadata"].get("Name", "")
            trials = wg["trials"]
            wind_sip_values[wind_name] = trials
        # print first 5 values of each wind SIP
        for wind_name, values in wind_sip_values.items():
            wind_sip_values[wind_name] = values
            # print(f"Wind SIP '{wind_name}' first 5 values: {values[:5]}")
        self.wind_sip_values = wind_sip_values
        adjusted_groups = []
        for sg in simulated_groups:
            inv_name = sg["metadata"].get("Name", "")
            baseline = np.array(sg["trials"], dtype=float)
            adjusted = baseline.copy()  # start from original baseline

            # Apply all winds cumulatively based on original trials
            for wind_name, inv_coeffs in wind_mappings.items():
                if inv_name not in inv_coeffs:
                    continue
                coeff = inv_coeffs[inv_name]
                wind_values = np.array(wind_sip_values.get(wind_name, []), dtype=float)

                if len(wind_values) == 0:
                    continue

                n = min(len(adjusted), len(wind_values))
                adjusted[:n] += coeff * wind_values[:n]

            # Create a copy of the simulation group with updated trials
            updated_group = sg.copy()
            updated_group["trials"] = adjusted.tolist()
            adjusted_groups.append(updated_group)

        # print the first 5 adjusted trials of each adjusted group
        # for ag in adjusted_groups:
            # print(f"Adjusted group '{ag['metadata'].get('Name', '')}' first 5 trials: {ag['trials'][:5]}")
        return adjusted_groups


def test_parser():
    # create test case to test the parser functionality
    test_parser = SIPParser("data/mock_sipmath_v2.xlsx")

    test_winds_parser = SIPParser("data/Winds_of_Fortune_Template.xlsx")

    test_winds_sip_parser = SIPParser("data/Winds_of_Fortune_SIP.xlsx")

    # test winds application
    adjusted_sips = test_parser.apply_winds(
        simulated_groups=test_parser.investments,
        template_groups=test_winds_parser.investments,
        wind_groups=test_winds_sip_parser.investments)



# main method to test current state of parser
if __name__ == "__main__":
    test_parser()