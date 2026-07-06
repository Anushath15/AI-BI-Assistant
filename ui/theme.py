from dataclasses import dataclass

@dataclass(frozen=True)
class Theme:
    # Brand
    PRIMARY = "#2563EB"
    PRIMARY_LIGHT = "#3B82F6"
    PRIMARY_DARK = "#1D4ED8"

    SUCCESS = "#16A34A"
    WARNING = "#F59E0B"
    ERROR = "#DC2626"
    INFO = "#0EA5E9"

    # Background
    BG = "#F8FAFC"
    SURFACE = "#FFFFFF"
    SIDEBAR = "#111827"

    # Text
    TEXT = "#111827"
    TEXT_LIGHT = "#6B7280"
    TEXT_WHITE = "#FFFFFF"

    BORDER = "#E5E7EB"

    SHADOW = "0 8px 24px rgba(0,0,0,0.08)"

    RADIUS = "18px"

theme = Theme()