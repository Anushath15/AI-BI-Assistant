import logging
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional

from models.analysis_result import AnalysisResult
from models.execution_plan import VisualizationConfig
from utils.logger import get_logger

logger = get_logger(__name__)

# Enterprise color palette
PALETTE = [
    "#2563EB",  # Primary blue
    "#16A34A",  # Success green
    "#7C3AED",  # Purple
    "#0891B2",  # Cyan
    "#D97706",  # Amber
    "#DC2626",  # Red
    "#0D9488",  # Teal
    "#9333EA",  # Violet
]

CHART_LAYOUT = dict(
    template="plotly_white",
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(l=20, r=20, t=45, b=20),
    height=380,
    font=dict(family="Inter, -apple-system, sans-serif", size=12, color="#374151"),
    title_font=dict(size=14, color="#111827", family="Inter, sans-serif"),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        borderwidth=0,
        font=dict(size=11),
    ),
    xaxis=dict(
        gridcolor="#F3F4F6",
        linecolor="#E5E7EB",
        tickfont=dict(size=11, color="#6B7280"),
    ),
    yaxis=dict(
        gridcolor="#F3F4F6",
        linecolor="#E5E7EB",
        tickfont=dict(size=11, color="#6B7280"),
    ),
)


def _apply_layout(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(**CHART_LAYOUT, title=title)
    return fig


class ChartEngine:

    def render(
        self,
        result: AnalysisResult,
        config: VisualizationConfig,
    ) -> Optional[go.Figure]:

        if not result.success or not result.data:
            return None

        df = pd.DataFrame(result.data)

        dispatch = {
            "bar":       self._bar,
            "line":      self._line,
            "pie":       self._pie,
            "scatter":   self._scatter,
            "histogram": self._histogram,
            "box":       self._box,
            "table":     self._table,
        }

        handler = dispatch.get(config.chart_type, self._table)

        try:
            return handler(df, config)
        except Exception as e:
            logger.exception("ChartEngine failed for %s", config.chart_type)
            return None

    def _bar(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        x = config.x_axis or df.columns[0]
        y = config.y_axis or df.columns[1] if len(df.columns) > 1 else df.columns[0]

        # Conditional coloring — green for high, red for low
        if len(df) == 1:
            colors = [PALETTE[0]]
        elif len(df) <= 2:
            colors = PALETTE[:len(df)]
        else:
            values = df[y].tolist()
            max_val = max(values)
            min_val = min(values)
            colors = []
            for v in values:
                if v == max_val:
                    colors.append("#16A34A")
                elif v == min_val:
                    colors.append("#DC2626")
                else:
                    colors.append("#2563EB")

        fig = go.Figure(go.Bar(
            x=df[x], y=df[y],
            marker_color=colors,
            marker_line_width=0,
            hovertemplate=f"<b>%{{x}}</b><br>{y}: %{{y:,.2f}}<extra></extra>",
        ))
        return _apply_layout(fig, config.title or "")

    def _line(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        x = config.x_axis or df.columns[0]
        y = config.y_axis or df.columns[1] if len(df.columns) > 1 else df.columns[0]

        fig = go.Figure(go.Scatter(
            x=df[x], y=df[y],
            mode="lines+markers",
            line=dict(color="#2563EB", width=2.5),
            marker=dict(color="#2563EB", size=6),
            fill="tozeroy",
            fillcolor="rgba(37,99,235,0.08)",
            hovertemplate=f"<b>%{{x}}</b><br>{y}: %{{y:,.2f}}<extra></extra>",
        ))
        return _apply_layout(fig, config.title or "")

    def _pie(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        names = config.x_axis or df.columns[0]
        values = config.y_axis or df.columns[1] if len(df.columns) > 1 else df.columns[0]

        fig = go.Figure(go.Pie(
            labels=df[names],
            values=df[values],
            marker=dict(colors=PALETTE),
            hole=0.35,
            hovertemplate="<b>%{label}</b><br>%{value:,.2f}<br>%{percent}<extra></extra>",
        ))
        return _apply_layout(fig, config.title or "")

    def _scatter(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        x = config.x_axis or df.columns[0]
        y = config.y_axis or df.columns[1] if len(df.columns) > 1 else df.columns[0]

        fig = go.Figure(go.Scatter(
            x=df[x], y=df[y],
            mode="markers",
            marker=dict(color="#2563EB", size=8, opacity=0.75),
            hovertemplate=f"{x}: %{{x}}<br>{y}: %{{y:,.2f}}<extra></extra>",
        ))
        return _apply_layout(fig, config.title or "")

    def _histogram(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        x = config.x_axis or df.columns[0]

        fig = go.Figure(go.Histogram(
            x=df[x],
            marker_color="#2563EB",
            marker_line_width=0,
        ))
        return _apply_layout(fig, config.title or "")

    def _box(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        y = config.y_axis or df.columns[0]

        fig = go.Figure(go.Box(
            y=df[y],
            marker_color="#2563EB",
            line_color="#1E40AF",
        ))
        return _apply_layout(fig, config.title or "")

    def _table(self, df: pd.DataFrame, config: VisualizationConfig) -> go.Figure:
        fig = go.Figure(go.Table(
            header=dict(
                values=[f"<b>{c}</b>" for c in df.columns],
                fill_color="#2563EB",
                font=dict(color="white", size=12),
                align="left",
                height=36,
            ),
            cells=dict(
                values=[df[c].tolist() for c in df.columns],
                fill_color=[["#F9FAFB", "white"] * (len(df) // 2 + 1)],
                font=dict(color="#111827", size=11),
                align="left",
                height=32,
            ),
        ))
        return _apply_layout(fig, config.title or "")