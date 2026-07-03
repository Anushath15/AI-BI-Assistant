def validate_dataframe(df):

    if df.empty:
        return False, "Dataset contains no records."

    if df.shape[1] == 0:
        return False, "Dataset contains no columns."

    return True, "Dataset is valid."

