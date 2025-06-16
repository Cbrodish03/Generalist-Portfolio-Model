import os

"""
A parser built for the Generalist-Portfolio-Model
Currently supports files of type: .xlsx
"""
class SIPParser:
    def __init__(self, filepath):
        self.filepath = filepath
        self.validate_file_type()
        
    def validate_file_type(self):
        """
        Checks the file extension of the given file
        """
        filename, ext = os.path.splitext(self.filepath)
        if ext.lower() != '.xlsx':
            raise ValueError(f"Invalid file type: {self.filepath}. Expected .xlsx (Excel) type")
        
        if ext.lower() == '.xlsx':
            self.parse_xlsx()
        
    def parse_xlsx(self):
        # TODO: to be implemented
        return

        
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

# main method to test current state of parser
if __name__ == "__main__":
    test_validation()

