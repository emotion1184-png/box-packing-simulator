# app/core/padding.py
"""
완충재 여유 계산
"""
from core.models import PaddingConfig

def apply_padding(inner_L: float, inner_W: float, inner_H: float, config: PaddingConfig) -> tuple[float, float, float]:
    """
    완충재 여유를 적용하여 유효 내경 계산
    Returns: (eff_L, eff_W, eff_H)
    Raises: ValueError if effective dimension <= 0
    """
    if not config.enabled:
        return (inner_L, inner_W, inner_H)
    
    eff_L = inner_L - 2 * config.padding_x
    eff_W = inner_W - 2 * config.padding_y
    eff_H = inner_H - 2 * config.padding_z
    
    if eff_L <= 0 or eff_W <= 0 or eff_H <= 0:
        raise ValueError(
            f"완충재 적용 후 유효 내경이 0 이하입니다. "
            f"(L:{eff_L:.1f}, W:{eff_W:.1f}, H:{eff_H:.1f})"
        )
    
    return (eff_L, eff_W, eff_H)
