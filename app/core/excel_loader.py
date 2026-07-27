"""박스 시뮬레이터용 Excel 카탈로그 로더."""

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from core.models import PackBox, ProductBox


LIST_SHEET = "리스트"
PACK_BOX_SHEET = "pack_boxes"
LEGACY_PRODUCT_SHEET = "product_boxes"


@dataclass
class CatalogLoadResult:
    pack_boxes: list[PackBox] | None
    product_boxes: list[ProductBox]
    product_sheet: str
    skipped_product_rows: int = 0


def _clean_text(value, fallback: str = "") -> str:
    if pd.isna(value):
        return fallback
    return str(value).strip()


def _optional_text(value) -> str | None:
    text = _clean_text(value)
    return text or None


def _as_bool(value, default: bool = True) -> bool:
    if pd.isna(value):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().casefold() not in {
        "false",
        "0",
        "n",
        "no",
        "아니오",
        "x",
    }


def _positive_float(value) -> float:
    number = float(value)
    if number <= 0:
        raise ValueError("박스 치수는 0보다 커야 합니다.")
    return number


def pack_boxes_from_dataframe(dataframe: pd.DataFrame) -> list[PackBox]:
    required = {
        "name",
        "inner_L",
        "inner_W",
        "inner_H",
        "outer_L",
        "outer_W",
        "outer_H",
    }
    missing = required.difference(dataframe.columns)
    if missing:
        raise ValueError(
            f"'{PACK_BOX_SHEET}' 시트 필수 열이 없습니다: {', '.join(sorted(missing))}"
        )

    boxes: list[PackBox] = []
    for _, row in dataframe.iterrows():
        boxes.append(
            PackBox(
                name=_clean_text(row["name"]),
                inner_L=_positive_float(row["inner_L"]),
                inner_W=_positive_float(row["inner_W"]),
                inner_H=_positive_float(row["inner_H"]),
                outer_L=_positive_float(row["outer_L"]),
                outer_W=_positive_float(row["outer_W"]),
                outer_H=_positive_float(row["outer_H"]),
                max_weight=(
                    float(row["max_weight"])
                    if "max_weight" in row and not pd.isna(row["max_weight"])
                    else None
                ),
                note=_optional_text(row.get("note")),
            )
        )
    return boxes


def products_from_list_dataframe(
    dataframe: pd.DataFrame,
) -> tuple[list[ProductBox], int]:
    """새 원본의 `리스트` 시트만 제품 카탈로그로 변환."""
    required = {"모델", "sku", "name", "l", "w", "h"}
    missing = required.difference(dataframe.columns)
    if missing:
        raise ValueError(
            f"'{LIST_SHEET}' 시트 필수 열이 없습니다: {', '.join(sorted(missing))}"
        )

    products: list[ProductBox] = []
    skipped = 0

    for _, row in dataframe.iterrows():
        try:
            model = _clean_text(row["모델"])
            sku = _clean_text(row["sku"])
            if not model or not sku:
                raise ValueError("모델 또는 SKU가 비어 있습니다.")

            products.append(
                ProductBox(
                    model=model,
                    sku=sku,
                    name=_clean_text(row["name"], fallback=model),
                    category=_optional_text(row.get("대분류")),
                    series=_optional_text(row.get("시리즈")),
                    l=_positive_float(row["l"]),
                    w=_positive_float(row["w"]),
                    h=_positive_float(row["h"]),
                    weight=(
                        float(row["weight"])
                        if "weight" in row and not pd.isna(row["weight"])
                        else None
                    ),
                    rotatable=_as_bool(row.get("rotatable"), default=True),
                    note=_optional_text(row.get("note")),
                )
            )
        except (TypeError, ValueError):
            skipped += 1

    if not products:
        raise ValueError(f"'{LIST_SHEET}' 시트에서 유효한 모델을 찾지 못했습니다.")

    return products, skipped


def products_from_legacy_dataframe(dataframe: pd.DataFrame) -> list[ProductBox]:
    column_map = {str(column).casefold(): column for column in dataframe.columns}
    required = {"sku", "name", "l", "w", "h"}
    missing = required.difference(column_map)
    if missing:
        raise ValueError(
            f"'{LEGACY_PRODUCT_SHEET}' 시트 필수 열이 없습니다: "
            f"{', '.join(sorted(missing))}"
        )

    products: list[ProductBox] = []
    for _, row in dataframe.iterrows():
        products.append(
            ProductBox(
                sku=_clean_text(row[column_map["sku"]]),
                name=_clean_text(row[column_map["name"]]),
                model=_optional_text(
                    row.get(column_map["model"]) if "model" in column_map else None
                ),
                l=_positive_float(row[column_map["l"]]),
                w=_positive_float(row[column_map["w"]]),
                h=_positive_float(row[column_map["h"]]),
                weight=(
                    float(row[column_map["weight"]])
                    if "weight" in column_map
                    and not pd.isna(row[column_map["weight"]])
                    else None
                ),
                rotatable=_as_bool(
                    row.get(column_map["rotatable"])
                    if "rotatable" in column_map
                    else None,
                    default=True,
                ),
                note=_optional_text(
                    row.get(column_map["note"]) if "note" in column_map else None
                ),
            )
        )
    return products


def load_catalog(
    source: str | Path | BinaryIO,
) -> CatalogLoadResult:
    """포장박스와 제품을 로드하되, 제품은 `리스트` 시트를 우선 사용."""
    workbook = pd.ExcelFile(source)
    sheet_names = set(workbook.sheet_names)

    pack_boxes = None
    if PACK_BOX_SHEET in sheet_names:
        pack_boxes = pack_boxes_from_dataframe(
            pd.read_excel(workbook, sheet_name=PACK_BOX_SHEET)
        )

    if LIST_SHEET in sheet_names:
        products, skipped = products_from_list_dataframe(
            pd.read_excel(workbook, sheet_name=LIST_SHEET)
        )
        return CatalogLoadResult(
            pack_boxes=pack_boxes,
            product_boxes=products,
            product_sheet=LIST_SHEET,
            skipped_product_rows=skipped,
        )

    if LEGACY_PRODUCT_SHEET in sheet_names:
        products = products_from_legacy_dataframe(
            pd.read_excel(workbook, sheet_name=LEGACY_PRODUCT_SHEET)
        )
        return CatalogLoadResult(
            pack_boxes=pack_boxes,
            product_boxes=products,
            product_sheet=LEGACY_PRODUCT_SHEET,
        )

    raise ValueError(
        f"제품 데이터 시트가 없습니다. '{LIST_SHEET}' 또는 "
        f"'{LEGACY_PRODUCT_SHEET}' 시트가 필요합니다."
    )
