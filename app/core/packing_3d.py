# app/core/packing_3d.py
"""
신뢰할 수 있는 3D Bin Packing 알고리즘 (py3dbp 대체)
Guillotine 3D 알고리즘 기반
"""
from typing import List, Tuple, Optional
from dataclasses import dataclass
import itertools

@dataclass
class Box3D:
    """3D 박스"""
    name: str
    l: float
    w: float
    h: float
    rotatable: bool = True
    
    def volume(self) -> float:
        return self.l * self.w * self.h
    
    def dimensions(self) -> Tuple[float, float, float]:
        return (self.l, self.w, self.h)
    
    def get_all_rotations(self) -> List[Tuple[float, float, float]]:
        """가능한 모든 회전 방향"""
        if not self.rotatable:
            return [(self.l, self.w, self.h)]
        
        # 6가지 회전
        dims = [self.l, self.w, self.h]
        rotations = set()
        for perm in itertools.permutations(dims):
            rotations.add(perm)
        return list(rotations)

@dataclass
class PackedItem:
    """적치된 아이템"""
    name: str
    position: Tuple[float, float, float]  # (x, y, z)
    dimension: Tuple[float, float, float]  # (l, w, h)
    rotation: str

@dataclass
class Space:
    """사용 가능한 공간"""
    x: float
    y: float
    z: float
    l: float
    w: float
    h: float
    
    def volume(self) -> float:
        return self.l * self.w * self.h
    
    def can_fit(self, box_l: float, box_w: float, box_h: float) -> bool:
        """박스가 이 공간에 들어갈 수 있는지"""
        return (box_l <= self.l + 0.01 and 
                box_w <= self.w + 0.01 and 
                box_h <= self.h + 0.01)

class Packer3D:
    """3D Bin Packing 알고리즘"""
    
    def __init__(self, bin_l: float, bin_w: float, bin_h: float):
        self.bin_l = bin_l
        self.bin_w = bin_w
        self.bin_h = bin_h
        self.packed_items: List[PackedItem] = []
        self.spaces: List[Space] = [Space(0, 0, 0, bin_l, bin_w, bin_h)]
    
    def pack_box(self, box: Box3D) -> bool:
        """박스를 적치 시도"""
        # 모든 회전 방향 시도
        rotations = box.get_all_rotations()
        
        best_space_idx = None
        best_rotation = None
        best_space_volume = float('inf')
        
        # 가장 작은 공간에 우선 배치 (Best Fit)
        for space_idx, space in enumerate(self.spaces):
            for rotation in rotations:
                box_l, box_w, box_h = rotation
                
                if space.can_fit(box_l, box_w, box_h):
                    if space.volume() < best_space_volume:
                        best_space_volume = space.volume()
                        best_space_idx = space_idx
                        best_rotation = rotation
        
        if best_space_idx is None:
            return False  # 들어갈 공간 없음
        
        # 박스 배치
        space = self.spaces[best_space_idx]
        box_l, box_w, box_h = best_rotation
        
        packed = PackedItem(
            name=box.name,
            position=(space.x, space.y, space.z),
            dimension=(box_l, box_w, box_h),
            rotation=f"{box_l:.0f}×{box_w:.0f}×{box_h:.0f}"
        )
        self.packed_items.append(packed)
        
        # 사용한 공간 제거
        del self.spaces[best_space_idx]
        
        # 남은 공간을 3개로 분할 (Guillotine split)
        new_spaces = []
        
        # 오른쪽 공간 (L 방향)
        if space.l > box_l + 0.01:
            new_spaces.append(Space(
                space.x + box_l,
                space.y,
                space.z,
                space.l - box_l,
                space.w,
                space.h
            ))
        
        # 앞쪽 공간 (W 방향)
        if space.w > box_w + 0.01:
            new_spaces.append(Space(
                space.x,
                space.y + box_w,
                space.z,
                box_l,
                space.w - box_w,
                space.h
            ))
        
        # 위쪽 공간 (H 방향) - 가장 중요!
        if space.h > box_h + 0.01:
            new_spaces.append(Space(
                space.x,
                space.y,
                space.z + box_h,
                box_l,
                box_w,
                space.h - box_h
            ))
        
        self.spaces.extend(new_spaces)
        
        # 공간 정렬 (부피가 큰 순서)
        self.spaces.sort(key=lambda s: s.volume(), reverse=True)
        
        return True
    
    def get_fill_ratio(self) -> float:
        """부피 효율"""
        used_volume = sum([item.dimension[0] * item.dimension[1] * item.dimension[2] 
                          for item in self.packed_items])
        bin_volume = self.bin_l * self.bin_w * self.bin_h
        return used_volume / bin_volume if bin_volume > 0 else 0


def pack_boxes_optimized(
    bin_dimension: Tuple[float, float, float],
    boxes: List[Box3D],
    max_trials: int = 10
) -> Tuple[List[PackedItem], List[Box3D]]:
    """
    최적화된 3D 박스 적치
    여러 정렬 전략을 시도하여 최선의 결과 반환
    """
    bin_l, bin_w, bin_h = bin_dimension
    
    strategies = [
        ('volume_desc', lambda b: -b.volume()),
        ('max_dim_desc', lambda b: -max(b.l, b.w, b.h)),
        ('height_desc', lambda b: -b.h),
        ('min_dim_desc', lambda b: -min(b.l, b.w, b.h)),
    ]
    
    best_packed = []
    best_unfitted = boxes.copy()
    best_fill_ratio = 0
    
    for trial in range(max_trials):
        strategy_name, sort_key = strategies[trial % len(strategies)]
        
        # 박스 정렬
        sorted_boxes = sorted(boxes, key=sort_key)
        
        # 패킹 시도
        packer = Packer3D(bin_l, bin_w, bin_h)
        unfitted = []
        
        for box in sorted_boxes:
            if not packer.pack_box(box):
                unfitted.append(box)
        
        # 더 나은 결과인지 확인
        if packer.get_fill_ratio() > best_fill_ratio:
            best_fill_ratio = packer.get_fill_ratio()
            best_packed = packer.packed_items
            best_unfitted = unfitted
    
    return best_packed, best_unfitted
