import pandas as pd

def load_csv(uploaded_file):
    """
    Load a CSV file and return (success, result).

    success = True  -> result is a DataFrame
    success = False -> result is an error message
    """
    try:
        df = pd.read_csv(uploaded_file)
        return True, df

    except pd.errors.EmptyDataError:
        return False, "The uploaded CSV file is empty."

    except pd.errors.ParserError:
        return False, "The CSV file is corrupted or has an invalid format."

    except UnicodeDecodeError:
        return False, "Unsupported file encoding. Please upload a UTF-8 encoded CSV."

    except Exception as e:
        return False, f"Unexpected error: {e}"