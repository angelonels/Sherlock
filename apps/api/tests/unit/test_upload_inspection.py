from io import BytesIO

import pytest
from openpyxl import Workbook

from app.core.config import Settings
from app.core.errors import ApiError
from app.services.csv_utils import detect_delimiter, detect_encoding, inspect_csv
from app.services.excel_utils import inspect_xlsx
from app.services.upload_safety import validate_extension, validate_file_size


def settings(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


def xlsx_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Orders"
    sheet.append(["Order Date", "Revenue"])
    sheet.append(["2026-01-01", 100])
    returns = workbook.create_sheet("Returns")
    returns.append(["Reason", "Count"])
    returns.append(["Damaged", 2])
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def test_csv_encoding_detection_uses_utf8_then_latin1() -> None:
    assert detect_encoding("name\nAman\n".encode()) == "utf-8-sig"
    assert detect_encoding("café\nAman\n".encode("latin-1")) == "latin-1"


def test_csv_delimiter_detection() -> None:
    assert detect_delimiter("a;b\n1;2\n") == ";"


def test_empty_csv_rejected() -> None:
    with pytest.raises(ApiError) as exc_info:
        inspect_csv(b"", settings())

    assert exc_info.value.code == "EMPTY_UPLOAD"


def test_headers_only_csv_rejected() -> None:
    with pytest.raises(ApiError) as exc_info:
        inspect_csv(b"name,revenue\n", settings())

    assert exc_info.value.code == "HEADERS_ONLY_UPLOAD"


def test_formula_like_values_are_detected() -> None:
    result = inspect_csv(b"name,note\nAman,=SUM(A1:A2)\n", settings())

    assert any(warning["code"] == "FORMULA_LIKE_VALUES_DETECTED" for warning in result["warnings"])


def test_wide_cells_are_rejected() -> None:
    with pytest.raises(ApiError) as exc_info:
        inspect_csv(b"name\nabcdef\n", settings(upload_max_cell_length=3))

    assert exc_info.value.code == "CELL_TOO_WIDE"


def test_xlsx_sheets_are_detected() -> None:
    result = inspect_xlsx(xlsx_bytes(), settings())

    assert result["sheet_names"] == ["Orders", "Returns"]
    assert result["recommended_sheet_name"] == "Orders"


def test_xlsx_selected_sheet_preview_works() -> None:
    result = inspect_xlsx(xlsx_bytes(), settings(), selected_sheet_name="Returns")

    assert result["selected_sheet_name"] == "Returns"
    assert result["preview_rows"] == [{"Reason": "Damaged", "Count": 2}]


def test_macro_enabled_excel_extension_is_rejected() -> None:
    with pytest.raises(ApiError) as exc_info:
        validate_extension("orders.xlsm")

    assert exc_info.value.code == "UNSUPPORTED_UPLOAD_TYPE"
    assert exc_info.value.status_code == 415


def test_other_unsupported_extension_is_rejected_with_415() -> None:
    with pytest.raises(ApiError) as exc_info:
        validate_extension("notes.txt")

    assert exc_info.value.code == "UNSUPPORTED_UPLOAD_TYPE"
    assert exc_info.value.status_code == 415


def test_oversized_upload_rejected() -> None:
    with pytest.raises(ApiError) as exc_info:
        validate_file_size(10, settings(upload_max_file_size_bytes=5))

    assert exc_info.value.status_code == 413
    assert exc_info.value.code == "UPLOAD_TOO_LARGE"
