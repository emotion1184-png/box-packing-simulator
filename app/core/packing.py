# app/core/packing.py
"""
박스 적치 계산 (자체 3D 알고리즘 사용)
"""
from core.models import PackBox, ProductBox, PaddingConfig, PackingResult, PackingItem
from core.padding import apply_padding
from core.packing_3d import Box3D, pack_boxes_optimized
from typing import List

def run_packing_simulation(
    pack_box: PackBox,
    product_selections: List[tuple[ProductBox, int]],  # [(product, qty), ...]
    padding_config: PaddingConfig,
    num_trials: int = 10
) -> PackingResult:
    """
    박스 적치 시뮬레이션 실행 (자체 알고리즘)
    """
    # 유효 내경 계산
    eff_L, eff_W, eff_H = apply_padding(
        pack_box.inner_L, pack_box.inner_W, pack_box.inner_H, padding_config
    )
    
    # Box3D 객체 생성
    boxes_to_pack = []
    product_by_item_name = {}
    for product_index, (prod, qty) in enumerate(product_selections):
        for i in range(qty):
            item_name = f"product_{product_index}_{i}"
            box = Box3D(
                name=item_name,
                l=prod.l,
                w=prod.w,
                h=prod.h,
                rotatable=prod.rotatable
            )
            boxes_to_pack.append(box)
            product_by_item_name[item_name] = prod
    
    # 패킹 수행
    packed, unfitted = pack_boxes_optimized(
        (eff_L, eff_W, eff_H),
        boxes_to_pack,
        max_trials=num_trials
    )
    
    # PackingItem 변환
    fitted_items = []
    for item in packed:
        prod = product_by_item_name[item.name]
        fitted_items.append(PackingItem(
            product_id=prod.product_id,
            sku=prod.sku,
            model=prod.model,
            name=prod.name,
            position=item.position,
            dimension=item.dimension,
            rotation_type=item.rotation
        ))
    
    # 미적치 집계
    unfitted_count = {}
    for box in unfitted:
        prod = product_by_item_name[box.name]
        if prod.product_id not in unfitted_count:
            unfitted_count[prod.product_id] = {
                'product_id': prod.product_id,
                'sku': prod.sku,
                'model': prod.model,
                'name': prod.name,
                'qty': 0,
            }
        unfitted_count[prod.product_id]['qty'] += 1
    
    unfitted_list = list(unfitted_count.values())
    
    # 부피 계산
    bin_volume = eff_L * eff_W * eff_H
    used_volume = sum([item.dimension[0] * item.dimension[1] * item.dimension[2] 
                      for item in fitted_items])
    fill_ratio = (used_volume / bin_volume) if bin_volume > 0 else 0
    remaining_volume = bin_volume - used_volume
    
    return PackingResult(
        pack_box_name=pack_box.name,
        effective_dimension=(eff_L, eff_W, eff_H),
        fitted_items=fitted_items,
        unfitted_items=unfitted_list,
        fill_ratio=fill_ratio,
        used_volume=used_volume,
        remaining_volume=remaining_volume,
        total_fitted_count=len(fitted_items),
        total_unfitted_count=sum([u['qty'] for u in unfitted_list])
    )
