import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

from models.analysis_result import AnalysisResult
from models.execution_plan import VisualizationConfig

logger = logging.getLogger(__name__)


class ChartEngine:

    def render(
        self,
        result: AnalysisResult,
        config: VisualizationConfig,
    ) -> Optional[go.Figure]:

        if not result.success or not result.data:
            return None

        df = pd.DataFrame(result.data)

        dispatch_map = {
            "bar":       self._bar,
            "line":      self._line,
            "pie":       self._pie,
            "scatter":   self._scatter,
            "histogram": self._histogram,
            "box":       self._box,
            "table":     self._table,
        }

        handler = dispatch_map.get(config.chart_type)

        if not handler:
            logger.warning("Unknown chart type: %s. Falling back to table.", config.chart_type)
            handler = self._table

        try:
            fig = handler(df, config)
            fig.update_layout(
                title=config.title or "",
                template="plotly_dark",
                height=450,
            )
            return fig
        except Exception as e:
            logger.exception("ChartEngine failed for chart type: %s", config.chart_type)
            return None

    # ------------------------------------------------------------------
    # Chart handlers
    # ------------------------------------------------------------------

    def _bar(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        x = config.x_axis or df.columns[0]
        y = config.y_axis or df.columns[1]
        return px.bar(df, x=x, y=y, title=config.title)

    def _line(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        x = config.x_axis or df.columns[0]
        y = config.y_axis or df.columns[1]
        return px.line(df, x=x, y=y, title=config.title)

    def _pie(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        names = config.x_axis or df.columns[0]
        values = config.y_axis or df.columns[1]
        return px.pie(df, names=names, values=values, title=config.title)

    def _scatter(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        x = config.x_axis or df.columns[0]
        y = config.y_axis or df.columns[1]
        return px.scatter(df, x=x, y=y, title=config.title)

    def _histogram(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        x = config.x_axis or df.columns[0]
        return px.histogram(df, x=x, title=config.title)

    def _box(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        y = config.y_axis or df.columns[0]
        return px.box(df, y=y, title=config.title)

    def _table(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=list(df.columns),
                        fill_color="#1f2937",
                        font_color="white",
                        align="left",
                    ),
                    cells=dict(
                        values=[df[c].tolist() for c in df.columns],
                        fill_color="#111827",
                        font_color="white",
                        align="left",
                    ),
                )
            ]
        )
        return fig