# app/core/models.py
"""
데이터 모델 정의 (Pydantic)
"""
from pydantic import BaseModel, Field
from typing import Optional

class PackBox(BaseModel):
    """포장박스 모델"""
    name: str = Field(..., description="포장박스 이름")
    inner_L: float = Field(..., gt=0, description="내경 길이(mm)")
    inner_W: float = Field(..., gt=0, description="내경 너비(mm)")
    inner_H: float = Field(..., gt=0, description="내경 높이(mm)")
    outer_L: float = Field(..., gt=0, description="외경 길이(mm)")
    outer_W: float = Field(..., gt=0, description="외경 너비(mm)")
    outer_H: float = Field(..., gt=0, description="외경 높이(mm)")
    max_weight: Optional[float] = Field(None, description="최대 중량(kg)")
    note: Optional[str] = Field(None, description="비고")

    def inner_volume(self) -> float:
        return self.inner_L * self.inner_W * self.inner_H

class ProductBox(BaseModel):
    """제품박스 모델"""
    sku: str = Field(..., description="SKU")
    name: str = Field(..., description="제품명")
    l: float = Field(..., gt=0, description="길이(mm)")
    w: float = Field(..., gt=0, description="너비(mm)")
    h: float = Field(..., gt=0, description="높이(mm)")
    weight: Optional[float] = Field(None, description="중량(kg)")
    rotatable: bool = Field(True, description="회전 허용 여부")
    note: Optional[str] = Field(None, description="비고")

    def volume(self) -> float:
        return self.l * self.w * self.h

class PaddingConfig(BaseModel):
    """완충재 여유 설정"""
    enabled: bool = Field(False, description="완충재 적용 여부")
    padding_x: float = Field(0, ge=0, description="X축 패딩(mm)")
    padding_y: float = Field(0, ge=0, description="Y축 패딩(mm)")
    padding_z: float = Field(0, ge=0, description="Z축 패딩(mm)")

class PackingItem(BaseModel):
    """적치된 아이템 정보"""
    sku: str
    name: str
    position: tuple[float, float, float]  # (x, y, z)
    dimension: tuple[float, float, float]  # (l, w, h) 회전 후
    rotation_type: str  # 회전 방향 설명

class PackingResult(BaseModel):
    """적치 결과"""
    pack_box_name: str
    effective_dimension: tuple[float, float, float]  # 유효 내경
    fitted_items: list[PackingItem]
    unfitted_items: list[dict]  # {sku, name, qty}
    fill_ratio: float
    used_volume: float
    remaining_volume: float
    total_fitted_count: int
    total_unfitted_count: int
