from models.analysis_step import AnalysisStep
from models.execution_plan import ExecutionPlan, Visualization

plan = ExecutionPlan(
    steps=[
        AnalysisStep(
            operation="filter",
            column="Region",
            operator="=",
            value="South"
        ),
        AnalysisStep(
            operation="group_by",
            column="Category"
        ),
        AnalysisStep(
            operation="aggregate",
            metric="Sales",
            aggregation="sum"
        )
    ],
    visualization=Visualization(
        chart_type="bar",
        x_axis="Category",
        y_axis="Sales"
    ),
    reasoning="Group sales by category for the South region."
)

print(plan)
