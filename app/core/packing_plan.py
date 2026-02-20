# app/core/packing_plan.py
"""
전체 제품을 담기 위한 포장박스 조합 계산
"""
from typing import List, Dict, Tuple
from core.models import PackBox, ProductBox, PaddingConfig, PackingResult
from core.packing import run_packing_simulation
import streamlit as st

class PackingPlan:
    """포장 계획 (여러 포장박스 조합)"""
    def __init__(self):
        self.box_usage: Dict[str, int] = {}  # {box_name: count}
        self.packed_details: List[PackingResult] = []
        self.total_boxes: int = 0
        self.total_volume: float = 0
        self.total_cost: float = 0
        self.all_packed: bool = False
        
def calculate_packing_plan(
    product_requirements: List[Tuple[ProductBox, int]],  # [(product, total_qty), ...]
    pack_boxes: List[PackBox],
    padding_config: PaddingConfig,
    strategy: str = "minimize_boxes",  # "minimize_boxes" or "maximize_efficiency"
    num_trials: int = 10
) -> PackingPlan:
    """
    전체 제품을 담기 위한 최적 포장박스 조합 계산
    
    Strategy:
    - minimize_boxes: 포장박스 개수 최소화
    - maximize_efficiency: 부피 효율 최대화
    """
    
    # 각 포장박스별로 얼마나 담을 수 있는지 시뮬레이션
    box_capacities = {}
    for pack_box in pack_boxes:
        try:
            result = run_packing_simulation(
                pack_box,
                product_requirements,
                padding_config,
                num_trials
            )
            
            # 각 제품별로 몇 개씩 담았는지 집계
            packed_by_sku = {}
            for item in result.fitted_items:
                packed_by_sku[item.sku] = packed_by_sku.get(item.sku, 0) + 1
            
            box_capacities[pack_box.name] = {
                'pack_box': pack_box,
                'result': result,
                'packed_by_sku': packed_by_sku,
                'total_packed': result.total_fitted_count,
                'fill_ratio': result.fill_ratio,
                'box_volume': pack_box.inner_volume()
            }
        except:
            continue
    
    if not box_capacities:
        return None
    
    # 남은 수량 추적
    remaining = {prod.sku: qty for prod, qty in product_requirements}
    
    plan = PackingPlan()
    
    # 탐욕 알고리즘으로 박스 선택
    max_iterations = 1000  # 무한 루프 방지
    iteration = 0
    
    while any(qty > 0 for qty in remaining.values()) and iteration < max_iterations:
        iteration += 1
        
        # 전략에 따라 최선의 박스 선택
        best_box = None
        best_score = -1
        
        for box_name, capacity in box_capacities.items():
            # 현재 남은 제품들에 대해 이 박스로 몇 개 담을 수 있는지
            can_pack = 0
            for sku, packed_qty in capacity['packed_by_sku'].items():
                can_pack += min(packed_qty, remaining.get(sku, 0))
            
            if can_pack == 0:
                continue
            
            # 점수 계산
            if strategy == "minimize_boxes":
                score = can_pack  # 많이 담을수록 좋음
            else:  # maximize_efficiency
                score = capacity['fill_ratio'] * can_pack
            
            if score > best_score:
                best_score = score
                best_box = box_name
        
        if best_box is None:
            break
        
        # 선택한 박스로 담기
        capacity = box_capacities[best_box]
        plan.box_usage[best_box] = plan.box_usage.get(best_box, 0) + 1
        plan.packed_details.append(capacity['result'])
        plan.total_boxes += 1
        plan.total_volume += capacity['box_volume']
        
        # 남은 수량 업데이트
        for sku, packed_qty in capacity['packed_by_sku'].items():
            if sku in remaining:
                remaining[sku] -= packed_qty
                if remaining[sku] < 0:
                    remaining[sku] = 0
    
    # 모두 담았는지 확인
    plan.all_packed = all(qty == 0 for qty in remaining.values())
    
    return plan


def get_multiple_packing_plans(
    product_requirements: List[Tuple[ProductBox, int]],
    pack_boxes: List[PackBox],
    padding_config: PaddingConfig,
    num_trials: int = 10
) -> List[Tuple[str, PackingPlan]]:
    """
    여러 전략으로 포장 계획 생성하여 비교
    Returns: [(strategy_name, plan), ...]
    """
    plans = []
    
    # 전략 1: 박스 개수 최소화
    plan1 = calculate_packing_plan(
        product_requirements,
        pack_boxes,
        padding_config,
        strategy="minimize_boxes",
        num_trials=num_trials
    )
    if plan1:
        plans.append(("Minimize Box Count", plan1))
    
    # 전략 2: 부피 효율 최대화
    plan2 = calculate_packing_plan(
        product_requirements,
        pack_boxes,
        padding_config,
        strategy="maximize_efficiency",
        num_trials=num_trials
    )
    if plan2:
        plans.append(("Maximize Fill Efficiency", plan2))
    
    return plans
