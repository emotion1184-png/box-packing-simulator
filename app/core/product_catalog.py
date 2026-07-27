"""제품 카탈로그의 검색, 표시, 선택 키 공통 로직."""

import re

from core.models import ProductBox


def parse_search_terms(text: str) -> list[str]:
    """줄바꿈, 쉼표, 세미콜론으로 구분한 검색어를 반환."""
    if not text or not text.strip():
        return []
    return [term.strip() for term in re.split(r"[\n,;]+", text) if term.strip()]


def filter_products(
    products: list[ProductBox],
    search_terms: list[str],
) -> list[ProductBox]:
    """모델명, SKU, 제품박스명, 분류, 시리즈에서 부분 일치 검색."""
    if not search_terms:
        return products

    normalized_terms = [term.casefold() for term in search_terms]
    matched: list[ProductBox] = []
    seen: set[str] = set()

    for product in products:
        target = " ".join(
            value
            for value in (
                product.model,
                product.sku,
                product.name,
                product.category,
                product.series,
            )
            if value
        ).casefold()

        if any(term in target for term in normalized_terms):
            if product.product_id not in seen:
                matched.append(product)
                seen.add(product.product_id)

    return matched


def product_label(product: ProductBox) -> str:
    """모델을 맨 앞에 둔 사용자용 선택 라벨."""
    if product.model:
        return f"{product.model} | {product.sku} | {product.name}"
    return f"{product.sku} | {product.name}"
