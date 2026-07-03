from models.analysis_step import AnalysisStep

step = AnalysisStep(
    operation="filter",
    column="Region",
    operator="=",
    value="South"
)

print(step)