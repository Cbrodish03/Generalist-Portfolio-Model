import os
import pandas as pd
import numpy as np


# ================================================================
# SIPParser
# A parser for SIPMath/Portfolio data files and Winds of Fortune.
# Supports:
#   • Standard SIP files
#   • Winds Template files
#   • Winds SIP files
# ================================================================
class SIPParser:
    def __init__(self, filepath):
        self.filepath = filepath

        # Initialize attributes (safe defaults)
        self.investments = []
        self.wind_mappings = {}  # wind_name → {investment_name: coefficient}
        self.wind_sip_values = {}  # wind_name → [trial values]

        # Parse immediately
        self.investments = self._dispatch_parse()

    # ================================================================
    # FILE ROUTING
    # Determines which parser to use based on file extension/content
    # ================================================================
    def _dispatch_parse(self):
        _, ext = os.path.splitext(self.filepath)

        if ext.lower() != ".xlsx":
            raise ValueError(f"Invalid file type ({ext}). Expected .xlsx format.")

        df = pd.read_excel(self.filepath, engine="calamine")

        basename = os.path.basename(self.filepath).lower()
        if "template" in basename:
            return self.parse_winds_template(df)

        return self.parse_standard_sip(df)

    # ================================================================
    # STANDARD SIP FILE PARSER
    # ================================================================
    def parse_standard_sip(self, df):
        """
        Parse a standard SIPMath file: metadata + trial columns.
        :param df: DataFrame of the SIP file
        :return: list of investment group data
        """
        meta_row, meta_col = self._locate_metadata(df)
        metadata_fields = self._extract_metadata_fields(df, meta_row, meta_col)
        trial_start, trial_count = self._locate_trials(df, meta_row)

        group_data = []
        col_idx = 0

        for col in df.columns[2:]:
            column_data = df[col].tolist()

            # Convert trial values
            trials = pd.to_numeric(
                column_data[trial_start: trial_start + trial_count],
                errors="coerce"
            )
            # skip empty investment columns
            if trials.tolist() == [np.nan] * trial_count:
                continue

            # Convert back to list, preserve NaNs
            trials = trials.tolist()

            # Extract metadata (aligned to metadata_fields)
            metadata_raw = column_data[
                           trial_start + trial_count:
                           trial_start + trial_count + len(metadata_fields)
                           ]
            metadata = dict(zip(metadata_fields, metadata_raw))

            group_data.append({
                "group_index": col_idx,
                "metadata": metadata,
                "trials": trials
            })
            col_idx += 1

        return group_data

    # --- HELPERS ----------------------------------------------------

    def _locate_metadata(self, df):
        """Find `Meta Data` cell in table."""
        for r in range(df.shape[0]):
            for c in range(df.shape[1]):
                if isinstance(df.iat[r, c], str) and df.iat[r, c].strip().lower() == "meta data":
                    return r, c
        raise ValueError("Could not find 'Meta Data' marker.")

    def _extract_metadata_fields(self, df, meta_row, meta_col):
        """Collect metadata fields under 'Meta Data' marker."""
        fields = []
        for r in range(meta_row + 1, df.shape[0]):
            val = df.iat[r, meta_col]
            if pd.isna(val) or str(val).strip() == "":
                break
            fields.append(str(val).strip())
        if not fields:
            raise ValueError("No metadata fields found under 'Meta Data'.")
        return fields

    def _locate_trials(self, df, meta_row):
        """Find the start of trials and count number of rows."""
        trial_start = None
        for r in range(meta_row, df.shape[0]):
            if str(df.iat[r, 1]).strip() == "1":
                trial_start = r
                break
        if trial_start is None:
            raise ValueError("Could not find trial index '1'.")

        trial_count = 0
        for v in df.iloc[trial_start:, 1].dropna():
            if not str(v).strip().isnumeric():
                break
            trial_count += 1

        return trial_start, trial_count

    # ================================================================
    # WINDS TEMPLATE PARSER
    # Reads investment → wind coefficient mappings
    # ================================================================
    def parse_winds_template(self, df):
        """Parse Winds of Fortune template mapping file."""
        header_row, header_col = self._locate_template_header(df)

        headers = df.iloc[header_row].fillna("").astype(str).tolist()
        wind_cols = [
            (c, headers[c]) for c in range(header_col + 1, len(headers))
        ]

        group_entries = []
        idx = 0

        for r in range(header_row + 1, df.shape[0]):
            name = df.iat[r, header_col]
            if pd.isna(name) or str(name).strip() == "":
                break  # End of investment list

            name = str(name).strip()

            winds = {}
            for col_idx, wind_name in wind_cols:
                coef = pd.to_numeric(df.iat[r, col_idx], errors="coerce")
                winds[wind_name] = float(coef) if not pd.isna(coef) else 0.0

            group_entries.append({
                "group_index": idx,
                "metadata": {
                    "Name": name,
                    "WindCoefficients": winds
                }
            })
            idx += 1

        return group_entries

    # --- HELPERS ----------------------------------------------------

    def _locate_template_header(self, df):
        """Find header row containing 'Investment' column."""
        for r in range(df.shape[0]):
            for c in range(df.shape[1]):
                val = df.iat[r, c]
                if isinstance(val, str) and val.strip().lower() in (
                        "investment", "investments", "investment name"
                ):
                    return r, c
        return 0, 0  # fallback

    # ================================================================
    # APPLY WINDS OF FORTUNE
    # ================================================================
    def apply_winds(self, simulated_groups, template_groups, wind_groups):
        """
        Apply Winds of Fortune adjustments:
            adjusted_trial[t] = base_trial[t] + coeff * wind_value[t]
        :param simulated_groups: the investment groups to adjust
        :param template_groups: the winds template groups defining relationships
        :param wind_groups: the wind SIP groups defining wind trial values
        :return: adjusted investment groups
        """
        self._build_wind_mappings(template_groups)
        self._build_wind_sip_values(wind_groups)

        adjusted = []
        for sim in simulated_groups:
            inv_name = sim["metadata"].get("Name", "")
            base = np.array(sim["trials"], dtype=float)
            result = base.copy()

            for wind_name, inv_coeffs in self.wind_mappings.items():
                if inv_name not in inv_coeffs:
                    continue

                coeff = inv_coeffs[inv_name]
                wind_values = np.array(self.wind_sip_values.get(wind_name, []))

                n = min(len(result), len(wind_values))
                result[:n] += coeff * wind_values[:n]

            modified = sim.copy()
            modified["trials"] = result.tolist()
            adjusted.append(modified)

        return adjusted

    # --- HELPERS ----------------------------------------------------

    def _build_wind_mappings(self, template_groups):
        """Build wind_name → investment_name → coefficient mapping."""
        mappings = {}
        for entry in template_groups:
            name = entry["metadata"]["Name"]
            for wind_name, coef in entry["metadata"]["WindCoefficients"].items():
                mappings.setdefault(wind_name, {})[name] = coef
        self.wind_mappings = mappings

    def _build_wind_sip_values(self, wind_groups):
        """Build wind_name → list of trial values."""
        self.wind_sip_values = {
            wg["metadata"]["Name"]: wg["trials"]
            for wg in wind_groups
        }
