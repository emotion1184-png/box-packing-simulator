# app/core/metrics.py
"""
KPI 메트릭 계산
"""
from core.models import PackingResult

def calculate_kpi(result: PackingResult) -> dict:
    """KPI 계산"""
    return {
        'total_fitted': result.total_fitted_count,
        'fill_ratio_pct': result.fill_ratio * 100,
        'remaining_volume': result.remaining_volume,
        'total_unfitted': result.total_unfitted_count
    }
