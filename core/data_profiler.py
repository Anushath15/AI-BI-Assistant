import pandas as pd
from models.dataset_profile import DatasetProfile


class DataProfiler:

    def profile(self, df: pd.DataFrame) -> DatasetProfile:

        return DatasetProfile(
            rows=len(df),
            columns=len(df.columns),
            column_names=list(df.columns),
            data_types=df.dtypes.astype(str).to_dict(),
            numeric_columns=list(df.select_dtypes(include="number").columns),
            categorical_columns=list(df.select_dtypes(include="object").columns),
            date_columns=list(df.select_dtypes(include="datetime").columns),
            missing_values=df.isnull().sum()[df.isnull().sum() > 0].to_dict(),
            sample_data=df.head(5).to_dict(orient="records"),
        )