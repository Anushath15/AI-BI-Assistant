import pandas as pd
import pytest
from models.dataset_profile import DatasetProfile
from core.business_knowledge import BusinessKnowledgeBuilder
from models.business_schema import BusinessSchema


def make_profile(**kwargs) -> DatasetProfile:
    defaults = dict(
        rows=100,
        columns=5,
        column_names=["Sales", "Profit", "Region", "Category", "Order Date"],
        data_types={"Sales": "float64", "Profit": "float64", "Region": "object", "Category": "object", "Order Date": "datetime64"},
        numeric_columns=["Sales", "Profit"],
        categorical_columns=["Region", "Category"],
        date_columns=["Order Date"],
        missing_values={},
        sample_data=[{"Sales": 100, "Profit": 20, "Region": "West", "Category": "Tech", "Order Date": "2023-01-01"}],
    )
    defaults.update(kwargs)
    return DatasetProfile(**defaults)


class TestBusinessKnowledgeBuilder:

    def test_returns_business_schema(self):
        profile = make_profile()
        schema = BusinessKnowledgeBuilder().build(profile, "test")
        assert isinstance(schema, BusinessSchema)

    def test_identifies_kpi_columns(self):
        profile = make_profile()
        schema = BusinessKnowledgeBuilder().build(profile, "test")
        assert "Sales" in schema.kpi_columns
        assert "Profit" in schema.kpi_columns

    def test_identifies_dimensions(self):
        profile = make_profile()
        schema = BusinessKnowledgeBuilder().build(profile, "test")
        assert "Region" in schema.dimensions
        assert "Category" in schema.dimensions

    def test_date_columns_not_in_dimensions(self):
        profile = make_profile()
        schema = BusinessKnowledgeBuilder().build(profile, "test")
        assert "Order Date" not in schema.dimensions

    def test_dataset_name_recorded(self):
        profile = make_profile()
        schema = BusinessKnowledgeBuilder().build(profile, "my_dataset")
        assert schema.dataset_name == "my_dataset"

    def test_business_summary_not_empty(self):
        profile = make_profile()
        schema = BusinessKnowledgeBuilder().build(profile, "test")
        assert len(schema.business_summary) > 0

    def test_aggregation_hints_for_measures(self):
        profile = make_profile()
        schema = BusinessKnowledgeBuilder().build(profile, "test")
        assert "Sales" in schema.aggregation_hints
        assert "Profit" in schema.aggregation_hints

    def test_empty_dataset_no_crash(self):
        profile = make_profile(
            column_names=["id"],
            numeric_columns=[],
            categorical_columns=[],
            date_columns=[],
            data_types={"id": "int64"},
            sample_data=[{"id": 1}],
        )
        schema = BusinessKnowledgeBuilder().build(profile, "empty")
        assert isinstance(schema, BusinessSchema)

    def test_id_columns_excluded_from_measures(self):
        profile = make_profile(
            column_names=["Row ID", "Sales"],
            numeric_columns=["Row ID", "Sales"],
            categorical_columns=[],
            date_columns=[],
            data_types={"Row ID": "int64", "Sales": "float64"},
            sample_data=[{"Row ID": 1, "Sales": 100}],
        )
        schema = BusinessKnowledgeBuilder().build(profile, "test")
        assert "Row ID" in schema.id_columns
        assert "Row ID" not in schema.measures