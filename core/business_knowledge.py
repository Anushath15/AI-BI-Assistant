from models.dataset_profile import DatasetProfile
from models.business_schema import BusinessSchema

# Keywords that suggest a column is a financial measure
MEASURE_KEYWORDS = [
    "sales", "revenue", "profit", "cost", "price", "amount",
    "total", "income", "expense", "margin", "discount", "tax",
    "quantity", "qty", "units", "count", "value", "budget",
]

# Keywords that suggest a column is a KPI
KPI_KEYWORDS = [
    "profit", "revenue", "sales", "margin", "growth",
    "conversion", "retention", "churn", "roi", "kpi",
]

# Keywords that suggest a column is an ID (not useful for analysis)
ID_KEYWORDS = [
    "id", "key", "code", "number", "no", "num", "ref", "index",
]

# Keywords that suggest a dimension (grouping column)
DIMENSION_KEYWORDS = [
    "region", "category", "segment", "type", "status", "name",
    "department", "branch", "city", "state", "country", "zone",
    "product", "customer", "employee", "channel", "brand",
]

# Aggregation hints per column type
AGGREGATION_HINTS = {
    "sales": "sum",
    "revenue": "sum",
    "profit": "sum",
    "cost": "sum",
    "quantity": "sum",
    "price": "mean",
    "discount": "mean",
    "margin": "mean",
}


class BusinessKnowledgeBuilder:

    def build(
        self,
        profile: DatasetProfile,
        dataset_name: str = "dataset",
    ) -> BusinessSchema:

        measures = []
        dimensions = []
        kpi_columns = []
        id_columns = []
        semantic_labels = {}
        aggregation_hints = {}

        for col in profile.column_names:
            col_lower = col.lower().replace(" ", "_")

            # Classify column
            is_numeric = col in profile.numeric_columns
            is_categorical = col in profile.categorical_columns
            is_date = col in profile.date_columns

            if is_date:
                semantic_labels[col] = "date"
                continue

            if self._matches_keywords(col_lower, ID_KEYWORDS):
                id_columns.append(col)
                semantic_labels[col] = "identifier"
                continue

            if is_numeric and self._matches_keywords(col_lower, MEASURE_KEYWORDS):
                measures.append(col)
                semantic_labels[col] = "measure"

                if self._matches_keywords(col_lower, KPI_KEYWORDS):
                    kpi_columns.append(col)
                    semantic_labels[col] = "kpi"

                for keyword, agg in AGGREGATION_HINTS.items():
                    if keyword in col_lower:
                        aggregation_hints[col] = agg
                        break
                else:
                    aggregation_hints[col] = "sum"

            elif is_categorical and self._matches_keywords(col_lower, DIMENSION_KEYWORDS):
                dimensions.append(col)
                semantic_labels[col] = "dimension"

            elif is_numeric:
                measures.append(col)
                semantic_labels[col] = "measure"
                aggregation_hints[col] = "sum"

            elif is_categorical:
                dimensions.append(col)
                semantic_labels[col] = "dimension"

        business_summary = self._generate_summary(
            dataset_name, measures, dimensions,
            kpi_columns, profile.date_columns
        )

        return BusinessSchema(
            dataset_name=dataset_name,
            measures=measures,
            dimensions=dimensions,
            date_columns=profile.date_columns,
            kpi_columns=kpi_columns,
            id_columns=id_columns,
            semantic_labels=semantic_labels,
            aggregation_hints=aggregation_hints,
            business_summary=business_summary,
        )

    def _matches_keywords(self, col_lower: str, keywords: list[str]) -> bool:
        return any(kw in col_lower for kw in keywords)

    def _generate_summary(
        self,
        name: str,
        measures: list[str],
        dimensions: list[str],
        kpis: list[str],
        dates: list[str],
    ) -> str:
        parts = [f"Dataset: {name}."]
        if kpis:
            parts.append(f"Key business metrics: {', '.join(kpis)}.")
        if measures:
            parts.append(f"Numeric measures: {', '.join(measures)}.")
        if dimensions:
            parts.append(f"Business dimensions for grouping: {', '.join(dimensions)}.")
        if dates:
            parts.append(f"Time columns: {', '.join(dates)}.")
        return " ".join(parts)