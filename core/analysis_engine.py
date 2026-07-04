import logging
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

from models.execution_plan import ExecutionPlan
from models.analysis_step import AnalysisStep
from models.analysis_result import AnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """
    Carries state between steps during execution.
    Replaces df.attrs — explicit, typed, never lost.
    """
    group_by_column: Optional[str] = None


class AnalysisEngine:

    def execute(
        self,
        df: pd.DataFrame,
        plan: ExecutionPlan,
        question: Optional[str] = None,
    ) -> AnalysisResult:

        working_df = df.copy()
        context = ExecutionContext()
        steps_run = 0

        try:
            for i, step in enumerate(plan.steps):
                logger.info("Executing step %d: %s", i + 1, step.operation)
                working_df = self._dispatch(step, working_df, context)
                steps_run += 1

            if working_df.empty:
                return AnalysisResult(
                    success=False,
                    question=question,
                    error="Analysis returned no results. Try a different question.",
                    execution_steps_run=steps_run,
                )

            return AnalysisResult(
                success=True,
                question=question,
                data=working_df.to_dict(orient="records"),
                row_count=len(working_df),
                columns=list(working_df.columns),
                execution_steps_run=steps_run,
            )

        except KeyError as e:
            logger.error("Column not found during execution: %s", e)
            return AnalysisResult(
                success=False,
                question=question,
                error=f"Column {e} not found in dataset. The AI may have used an incorrect column name.",
                execution_steps_run=steps_run,
            )

        except Exception as e:
            logger.exception("AnalysisEngine failed at step %d", steps_run + 1)
            return AnalysisResult(
                success=False,
                question=question,
                error=f"Execution failed at step {steps_run + 1}: {e}",
                execution_steps_run=steps_run,
            )

    def _dispatch(
        self,
        step: AnalysisStep,
        df: pd.DataFrame,
        context: ExecutionContext,
    ) -> pd.DataFrame:

        dispatch_map = {
            "filter":       self._filter,
            "group_by":     self._group_by,
            "aggregate":    self._aggregate,
            "sort":         self._sort,
            "limit":        self._limit,
            "top_n":        self._limit,
            "bottom_n":     self._bottom_n,
            "distribution": self._distribution,
            "correlation":  self._correlation,
            "kpi":          self._kpi,
            "time_series":  self._time_series,
            "compare":      self._group_by,
        }

        handler = dispatch_map.get(step.operation)
        if not handler:
            raise ValueError(f"No handler for operation: {step.operation}")
        return handler(step, df, context)

    def _filter(
        self,
        step: AnalysisStep,
        df: pd.DataFrame,
        context: ExecutionContext,
    ) -> pd.DataFrame:

        col = step.column
        op = step.operator
        val = step.value

        ops = {
            "=":   lambda: df[df[col] == val],
            "!=":  lambda: df[df[col] != val],
            ">":   lambda: df[df[col] > val],
            "<":   lambda: df[df[col] < val],
            ">=":  lambda: df[df[col] >= val],
            "<=":  lambda: df[df[col] <= val],
            "contains":   lambda: df[df[col].astype(str).str.contains(str(val), case=False, na=False)],
            "startswith": lambda: df[df[col].astype(str).str.startswith(str(val), na=False)],
            "endswith":   lambda: df[df[col].astype(str).str.endswith(str(val), na=False)],
            "year_equals":  lambda: df[pd.to_datetime(df[col], errors="coerce").dt.year == int(val)],
            "month_equals": lambda: df[pd.to_datetime(df[col], errors="coerce").dt.month == int(val)],
        }

        handler = ops.get(op)
        if not handler:
            raise ValueError(f"Unsupported filter operator: {op}")
        return handler()

    def _group_by(
        self,
        step: AnalysisStep,
        df: pd.DataFrame,
        context: ExecutionContext,
    ) -> pd.DataFrame:
        context.group_by_column = step.column
        return df

    def _aggregate(
        self,
        step: AnalysisStep,
        df: pd.DataFrame,
        context: ExecutionContext,
    ) -> pd.DataFrame:

        group_col = context.group_by_column
        metric = step.metric
        agg = step.aggregation

        agg_map = {
            "sum": "sum", "mean": "mean", "count": "count",
            "min": "min", "max": "max", "median": "median", "std": "std",
        }

        if agg not in agg_map:
            raise ValueError(f"Unsupported aggregation: {agg}")

        if group_col:
            result = (
                df.groupby(group_col)[metric]
                .agg(agg_map[agg])
                .reset_index()
            )
            result.columns = [group_col, metric]
        else:
            value = getattr(df[metric], agg_map[agg])()
            result = pd.DataFrame([{metric: value}])

        return result

    def _sort(
        self,
        step: AnalysisStep,
        df: pd.DataFrame,
        context: ExecutionContext,
    ) -> pd.DataFrame:
        ascending = step.order != "descending"
        col = step.column or df.columns[-1]
        return df.sort_values(by=col, ascending=ascending).reset_index(drop=True)

    def _limit(
        self,
        step: AnalysisStep,
        df: pd.DataFrame,
        context: ExecutionContext,
    ) -> pd.DataFrame:
        return df.head(step.n or 10)

    def _bottom_n(
        self,
        step: AnalysisStep,
        df: pd.DataFrame,
        context: ExecutionContext,
    ) -> pd.DataFrame:
        return df.tail(step.n or 10)

    def _distribution(
        self,
        step: AnalysisStep,
        df: pd.DataFrame,
        context: ExecutionContext,
    ) -> pd.DataFrame:
        col = step.column
        counts = df[col].value_counts().reset_index()
        counts.columns = [col, "count"]
        return counts

    def _correlation(
        self,
        step: AnalysisStep,
        df: pd.DataFrame,
        context: ExecutionContext,
    ) -> pd.DataFrame:
        numeric_df = df.select_dtypes(include="number")
        corr = numeric_df.corr().reset_index()
        corr = corr.rename(columns={"index": "column"})
        return corr

    def _kpi(
        self,
        step: AnalysisStep,
        df: pd.DataFrame,
        context: ExecutionContext,
    ) -> pd.DataFrame:
        metric = step.metric
        agg = step.aggregation or "sum"
        value = getattr(df[metric], agg)()
        return pd.DataFrame([{metric: value, "aggregation": agg}])

    def _time_series(
        self,
        step: AnalysisStep,
        df: pd.DataFrame,
        context: ExecutionContext,
    ) -> pd.DataFrame:
        date_col = step.column
        metric = step.metric
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        result = (
            df.groupby(df[date_col].dt.to_period("M"))[metric]
            .sum()
            .reset_index()
        )
        result[date_col] = result[date_col].astype(str).str[:7]
        return result