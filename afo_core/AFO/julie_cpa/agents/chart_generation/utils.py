"""Chart Generation Utilities.

플롯 변환 및 공통 유틸리티 함수.
"""

from __future__ import annotations

import base64
from io import BytesIO
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import matplotlib.pyplot as plt


def convert_plot_to_data(fig: plt.Figure, output_format: str) -> str:
    """matplotlib figure를 데이터로 변환.

    Args:
        fig: matplotlib Figure 객체
        output_format: 출력 포맷 (png, svg, pdf)

    Returns:
        Base64 인코딩된 이미지 데이터 또는 SVG 문자열
    """
    buffer = BytesIO()

    if output_format == "png":
        fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{image_data}"

    elif output_format == "svg":
        fig.savefig(buffer, format="svg", bbox_inches="tight")
        buffer.seek(0)
        return buffer.getvalue().decode("utf-8")

    elif output_format == "pdf":
        fig.savefig(buffer, format="pdf", bbox_inches="tight")
        buffer.seek(0)
        pdf_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:application/pdf;base64,{pdf_data}"

    else:
        # 기본적으로 PNG
        fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
        buffer.seek(0)
        image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{image_data}"


def calculate_tax_rate(income: float) -> float:
    """소득에 따른 세율 계산.

    Args:
        income: 연 소득

    Returns:
        세율 (0.0 ~ 1.0)
    """
    if income > 200000:
        return 0.30
    elif income > 100000:
        return 0.25
    elif income > 50000:
        return 0.20
    else:
        return 0.12


def format_currency(amount: float) -> str:
    """금액을 통화 형식으로 포맷.

    Args:
        amount: 금액

    Returns:
        포맷된 문자열 (예: "$1,234.56")
    """
    return f"${amount:,.2f}"
