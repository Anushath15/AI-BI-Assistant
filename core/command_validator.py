from models.analysis_command import AnalysisCommand


class CommandValidator:
    """
    Validates AI-generated analysis commands before execution.
    """

    ALLOWED_OPERATIONS = {
        "groupby",
        "aggregate",
        "filter",
        "sort",
        "top_n",
        "bottom_n",
        "time_series",
        "compare",
        "distribution"
    }

    ALLOWED_AGGREGATIONS = {
        "sum",
        "mean",
        "count",
        "min",
        "max",
        "median"
    }

    ALLOWED_CHARTS = {
        "bar",
        "line",
        "pie",
        "scatter",
        "histogram",
        "table"
    }

    def validate(self, command: AnalysisCommand, profile):

        errors = []

        # Validate operation
        if command.operation not in self.ALLOWED_OPERATIONS:
            errors.append(
                f"Unsupported operation: {command.operation}"
            )

        # Validate group_by column
        if command.group_by:
            if command.group_by not in profile["column_names"]:
                errors.append(
                    f"Unknown column: {command.group_by}"
                )

        # Validate metric column
        if command.metric:
            if command.metric not in profile["column_names"]:
                errors.append(
                    f"Unknown metric: {command.metric}"
                )

        # Validate aggregation
        if command.aggregation:
            if command.aggregation not in self.ALLOWED_AGGREGATIONS:
                errors.append(
                    f"Unsupported aggregation: {command.aggregation}"
                )

        # Validate chart
        if command.chart:
            if command.chart not in self.ALLOWED_CHARTS:
                errors.append(
                    f"Unsupported chart: {command.chart}"
                )

        return len(errors) == 0, errors