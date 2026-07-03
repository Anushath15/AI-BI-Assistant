import pandas as pd


class DataCleaner:
    """
    Handles all dataset preprocessing before analysis.
    """

    def __init__(self):
        self.report = {
            "missing_values": {},
            "duplicates_removed": 0,
            "date_columns": []
        }

    def detect_missing_values(self, df):
        """
        Detect missing values in each column.
        """

        missing = df.isnull().sum()

        self.report["missing_values"] = (
            missing[missing > 0].to_dict()
        )

        return df

    def remove_duplicates(self, df):
        """
        Remove duplicate rows.
        """

        before = len(df)

        df = df.drop_duplicates()

        after = len(df)

        self.report["duplicates_removed"] = before - after

        return df

    def parse_dates(self, df):
        """
        Convert only columns that contain 'date'
        in their name.
        """

        for column in df.columns:

            if "date" in column.lower():

                try:

                    df[column] = pd.to_datetime(
                        df[column],
                        errors="coerce"
                    )

                    self.report["date_columns"].append(column)

                except Exception:
                    pass

        return df

    def clean(self, df):
        """
        Execute complete cleaning pipeline.
        """

        df = self.detect_missing_values(df)

        df = self.remove_duplicates(df)

        df = self.parse_dates(df)

        return df, self.report