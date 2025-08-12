"""Tests for the DarmaApiService."""

import datetime
import tempfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from ageing_analysis.services.darma_api_service import DarmaApiSchema, DarmaApiService


class TestDarmaApiService:
    """Test cases for DarmaApiService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = DarmaApiService()

    def test_create_input_file_basic(self):
        """Test basic input file creation with all parameters."""
        # Arrange
        time_from = datetime.datetime(2025, 7, 1, 0, 0, 1)
        time_to = datetime.datetime(2025, 7, 2, 23, 59, 59)
        schema = DarmaApiSchema.FT0ARCH
        elements = [
            "ft0_dcs:FEE/PMA0/Ch01.actual.CFD_RATE",
            "ft0_dcs:FEE/PMA0/Ch02.actual.CFD_RATE",
        ]

        # Act
        result_path = self.service._create_input_file(
            time_from, time_to, schema, elements
        )

        # Assert
        assert isinstance(result_path, Path)
        assert result_path.exists()
        assert result_path.suffix == ".csv"
        assert "darma_input_" in result_path.name

        # Check file content - pandas adds trailing semicolons and empty columns
        with open(result_path, encoding="utf-8") as f:
            content = f.read()

        # Split by lines and check each line contains expected content
        lines = content.strip().split("\n")
        assert len(lines) == 4

        assert lines[0].startswith("timefrom;01.07.2025;00:00:01.0")
        assert lines[1].startswith("timeto;02.07.2025;23:59:59.0")
        assert lines[2].startswith("schema;FT0ARCH")
        assert lines[3].startswith(
            "element;ft0_dcs:FEE/PMA0/Ch01.actual.CFD_RATE;"
            "ft0_dcs:FEE/PMA0/Ch02.actual.CFD_RATE"
        )

        # Cleanup
        result_path.unlink()

    def test_create_input_file_empty_elements(self):
        """Test input file creation with empty elements list."""
        # Arrange
        time_from = datetime.datetime(2025, 7, 1, 0, 0, 1)
        time_to = datetime.datetime(2025, 7, 2, 23, 59, 59)
        schema = DarmaApiSchema.FT0ARCH
        elements = []

        # Act
        result_path = self.service._create_input_file(
            time_from, time_to, schema, elements
        )

        # Assert
        with open(result_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.strip().split("\n")
        assert len(lines) == 3

        assert lines[0].startswith("timefrom;01.07.2025;00:00:01.0")
        assert lines[1].startswith("timeto;02.07.2025;23:59:59.0")
        assert lines[2].startswith("schema;FT0ARCH")
        assert "element;" not in content

        # Cleanup
        result_path.unlink()

    def test_create_input_file_different_date_formats(self):
        """Test input file creation with different date formats."""
        # Arrange
        time_from = datetime.datetime(2024, 12, 31, 12, 30, 45)
        time_to = datetime.datetime(2025, 1, 1, 15, 45, 30)
        schema = DarmaApiSchema.FT0ARCH
        elements = ["test_element"]

        # Act
        result_path = self.service._create_input_file(
            time_from, time_to, schema, elements
        )

        # Assert
        with open(result_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.strip().split("\n")
        assert len(lines) == 4

        assert lines[0].startswith("timefrom;31.12.2024;12:30:45.0")
        assert lines[1].startswith("timeto;01.01.2025;15:45:30.0")
        assert lines[2].startswith("schema;FT0ARCH")
        assert lines[3].startswith("element;test_element")

        # Cleanup
        result_path.unlink()

    def test_create_input_file_many_elements(self):
        """Test input file creation with many elements."""
        # Arrange
        time_from = datetime.datetime(2025, 7, 1, 0, 0, 1)
        time_to = datetime.datetime(2025, 7, 2, 23, 59, 59)
        schema = DarmaApiSchema.FT0ARCH
        elements = [f"ft0_dcs:FEE/PMA0/Ch{i:02d}.actual.CFD_RATE" for i in range(1, 11)]

        # Act
        result_path = self.service._create_input_file(
            time_from, time_to, schema, elements
        )

        # Assert
        with open(result_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.strip().split("\n")
        assert len(lines) == 4  # timefrom, timeto, schema, element

        # Check element line
        element_line = lines[3]
        assert element_line.startswith("element;")
        assert "ft0_dcs:FEE/PMA0/Ch01.actual.CFD_RATE" in element_line
        assert "ft0_dcs:FEE/PMA0/Ch10.actual.CFD_RATE" in element_line

        # Cleanup
        result_path.unlink()

    def test_create_input_file_temp_directory(self):
        """Test that file is created in the system's temporary directory."""
        # Arrange
        time_from = datetime.datetime(2025, 7, 1, 0, 0, 1)
        time_to = datetime.datetime(2025, 7, 2, 23, 59, 59)
        schema = DarmaApiSchema.FT0ARCH
        elements = ["test_element"]

        # Act
        result_path = self.service._create_input_file(
            time_from, time_to, schema, elements
        )

        # Assert
        temp_dir = Path(tempfile.gettempdir())
        assert result_path.parent == temp_dir
        assert result_path.name.startswith("darma_input_")
        assert result_path.name.endswith(".csv")

        # Cleanup
        result_path.unlink()

    def test_create_input_file_unique_filenames(self):
        """Test that multiple calls create files with unique names."""
        # Arrange
        time_from = datetime.datetime(2025, 7, 1, 0, 0, 1)
        time_to = datetime.datetime(2025, 7, 2, 23, 59, 59)
        schema = DarmaApiSchema.FT0ARCH
        elements = ["test_element"]

        # Act
        result_path1 = self.service._create_input_file(
            time_from, time_to, schema, elements
        )
        result_path2 = self.service._create_input_file(
            time_from, time_to, schema, elements
        )

        # Assert
        assert result_path1 != result_path2
        assert result_path1.name != result_path2.name
        assert result_path1.exists()
        assert result_path2.exists()

        # Cleanup
        result_path1.unlink()
        result_path2.unlink()

    def test_create_input_file_encoding(self):
        """Test that file is created with UTF-8 encoding."""
        # Arrange
        time_from = datetime.datetime(2025, 7, 1, 0, 0, 1)
        time_to = datetime.datetime(2025, 7, 2, 23, 59, 59)
        schema = DarmaApiSchema.FT0ARCH
        elements = ["test_element"]

        # Act
        result_path = self.service._create_input_file(
            time_from, time_to, schema, elements
        )

        # Assert
        # Try to read with different encodings - UTF-8 should work
        with open(result_path, encoding="utf-8") as f:
            content_utf8 = f.read()

        # Should be able to read the content
        assert "timefrom" in content_utf8
        assert "schema;FT0ARCH" in content_utf8

        # Cleanup
        result_path.unlink()

    def test_create_input_file_edge_case_midnight(self):
        """Test input file creation with midnight times."""
        # Arrange
        time_from = datetime.datetime(2025, 7, 1, 0, 0, 0)
        time_to = datetime.datetime(2025, 7, 1, 23, 59, 59)
        schema = DarmaApiSchema.FT0ARCH
        elements = ["test_element"]

        # Act
        result_path = self.service._create_input_file(
            time_from, time_to, schema, elements
        )

        # Assert
        with open(result_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.strip().split("\n")
        assert len(lines) == 4

        assert lines[0].startswith("timefrom;01.07.2025;00:00:00.0")
        assert lines[1].startswith("timeto;01.07.2025;23:59:59.0")
        assert lines[2].startswith("schema;FT0ARCH")
        assert lines[3].startswith("element;test_element")

        # Cleanup
        result_path.unlink()

    def test_create_input_file_special_characters(self):
        """Test input file creation with special characters in elements."""
        # Arrange
        time_from = datetime.datetime(2025, 7, 1, 0, 0, 1)
        time_to = datetime.datetime(2025, 7, 2, 23, 59, 59)
        schema = DarmaApiSchema.FT0ARCH
        elements = ["ft0_dcs:FEE/PMA0/Ch01.actual.CFD_RATE", "test:with:colons"]

        # Act
        result_path = self.service._create_input_file(
            time_from, time_to, schema, elements
        )

        # Assert
        with open(result_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.strip().split("\n")
        assert len(lines) == 4

        assert lines[0].startswith("timefrom;01.07.2025;00:00:01.0")
        assert lines[1].startswith("timeto;02.07.2025;23:59:59.0")
        assert lines[2].startswith("schema;FT0ARCH")
        assert lines[3].startswith(
            "element;ft0_dcs:FEE/PMA0/Ch01.actual.CFD_RATE;test:with:colons"
        )

        # Cleanup
        result_path.unlink()

    def test_parse_response_basic(self):
        """Test basic response parsing with valid data."""
        # Arrange
        # Use the format expected by the implementation: YYYY-MM-DD
        csv_content = """date;time;element_name/alias;value
2025-07-01;00:00:01;ft0_dcs:FEE/PMA0/Ch01.actual.CFD_RATE;123.45
2025-07-02;12:30:45;ft0_dcs:FEE/PMA0/Ch02.actual.CFD_RATE;67.89"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            temp_file_path = Path(f.name)

        # Act
        result = self.service._parse_response(temp_file_path)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ["timestamp", "value", "element_name"]

        # Check first datapoint
        assert result.iloc[0]["timestamp"] == pd.Timestamp("2025-07-01 00:00:01")
        assert result.iloc[0]["value"] == 123.45
        assert result.iloc[0]["element_name"] == "ft0_dcs:FEE/PMA0/Ch01.actual.CFD_RATE"

        # Check second datapoint
        assert result.iloc[1]["timestamp"] == pd.Timestamp("2025-07-02 12:30:45")
        assert result.iloc[1]["value"] == 67.89
        assert result.iloc[1]["element_name"] == "ft0_dcs:FEE/PMA0/Ch02.actual.CFD_RATE"

        # Cleanup
        temp_file_path.unlink()

    def test_parse_response_with_header(self):
        """Test response parsing with header line."""
        # Arrange
        csv_content = """date;time;element_name/alias;value
2025-07-01;00:00:01;test_element;123.45"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            temp_file_path = Path(f.name)

        # Act
        result = self.service._parse_response(temp_file_path)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]["timestamp"] == pd.Timestamp("2025-07-01 00:00:01")
        assert result.iloc[0]["value"] == 123.45
        assert result.iloc[0]["element_name"] == "test_element"

        # Cleanup
        temp_file_path.unlink()

    def test_parse_response_empty_file(self):
        """Test response parsing with empty file."""
        # Arrange
        csv_content = ""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            temp_file_path = Path(f.name)

        # Act
        result = self.service._parse_response(temp_file_path)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == ["timestamp", "value", "element_name"]

        # Cleanup
        temp_file_path.unlink()

    def test_parse_response_only_header(self):
        """Test response parsing with only header line."""
        # Arrange
        csv_content = "date;time;element_name/alias;value"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            temp_file_path = Path(f.name)

        # Act
        result = self.service._parse_response(temp_file_path)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == ["timestamp", "value", "element_name"]

        # Cleanup
        temp_file_path.unlink()

    def test_parse_response_malformed_lines(self):
        """Test response parsing with malformed lines."""
        # Arrange
        csv_content = """date;time;element_name/alias;value
2025-07-01;00:00:01;test_element;123.45
malformed_line
2025-07-01;00:00:02;test_element2;67.89
another_malformed_line_with_too_many_parts;part2;part3;part4;part5
2025-07-01;00:00:03;test_element3;99.99"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            temp_file_path = Path(f.name)

        # Act
        result = self.service._parse_response(temp_file_path)

        # Assert
        # Malformed lines are skipped; valid lines are kept
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert list(result.columns) == ["timestamp", "value", "element_name"]
        assert result.iloc[0]["value"] == 123.45
        assert result.iloc[1]["value"] == 67.89
        assert result.iloc[2]["value"] == 99.99

        # Cleanup
        temp_file_path.unlink()

    def test_parse_response_invalid_date_format(self):
        """Test response parsing with invalid date format."""
        # Arrange
        csv_content = """date;time;element_name/alias;value
2025-07-01;00:00:01;test_element;123.45
invalid_date;00:00:02;test_element2;67.89
2025-07-01;invalid_time;test_element3;99.99"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            temp_file_path = Path(f.name)

        # Act
        result = self.service._parse_response(temp_file_path)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1  # Only the first valid line should be parsed
        assert result.iloc[0]["value"] == 123.45

        # Cleanup
        temp_file_path.unlink()

    def test_parse_response_invalid_value_format(self):
        """Test response parsing with invalid value format."""
        # Arrange
        csv_content = """date;time;element_name/alias;value
2025-07-01;00:00:01;test_element;123.45
2025-07-01;00:00:02;test_element2;not_a_number
2025-07-01;00:00:03;test_element3;67.89"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            temp_file_path = Path(f.name)

        # Act
        result = self.service._parse_response(temp_file_path)

        # Assert
        # Non-numeric values are skipped; valid rows remain
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert result.iloc[0]["value"] == 123.45
        assert result.iloc[1]["value"] == 67.89

        # Cleanup
        temp_file_path.unlink()

    def test_parse_response_empty_lines(self):
        """Test response parsing with empty lines."""
        # Arrange
        csv_content = """date;time;element_name/alias;value

2025-07-01;00:00:01;test_element;123.45

2025-07-01;00:00:02;test_element2;67.89

"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            temp_file_path = Path(f.name)

        # Act
        result = self.service._parse_response(temp_file_path)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2  # Empty lines should be skipped
        assert result.iloc[0]["value"] == 123.45
        assert result.iloc[1]["value"] == 67.89

        # Cleanup
        temp_file_path.unlink()

    def test_parse_response_different_time_formats(self):
        """Test response parsing with different time formats."""
        # Arrange
        csv_content = """date;time;element_name/alias;value
2025-07-01;00:00:00;test_element;123.45
2025-07-01;23:59:59;test_element2;67.89
2024-12-31;12:30:45;test_element3;99.99"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            temp_file_path = Path(f.name)

        # Act
        result = self.service._parse_response(temp_file_path)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

        # Check timestamps
        assert result.iloc[0]["timestamp"] == pd.Timestamp("2025-07-01 00:00:00")
        assert result.iloc[1]["timestamp"] == pd.Timestamp("2025-07-01 23:59:59")
        assert result.iloc[2]["timestamp"] == pd.Timestamp("2024-12-31 12:30:45")

        # Cleanup
        temp_file_path.unlink()

    def test_parse_response_special_characters_in_element_name(self):
        """Test response parsing with special characters in element names."""
        # Arrange
        csv_content = """date;time;element_name/alias;value
2025-07-01;00:00:01;ft0_dcs:FEE/PMA0/Ch01.actual.CFD_RATE;123.45
2025-07-01;00:00:02;test:with:colons;67.89
2025-07-01;00:00:03;test_with_underscores;99.99"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            temp_file_path = Path(f.name)

        # Act
        result = self.service._parse_response(temp_file_path)

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

        # Check element names
        assert result.iloc[0]["element_name"] == "ft0_dcs:FEE/PMA0/Ch01.actual.CFD_RATE"
        assert result.iloc[1]["element_name"] == "test:with:colons"
        assert result.iloc[2]["element_name"] == "test_with_underscores"

        # Cleanup
        temp_file_path.unlink()

    def test_create_input_file_with_aliases(self):
        """Test input file creation with aliases."""
        # Arrange
        time_from = datetime.datetime(2025, 7, 1, 0, 0, 1)
        time_to = datetime.datetime(2025, 7, 2, 23, 59, 59)
        schema = DarmaApiSchema.FT0ARCH
        elements = [
            "ft0_dcs:FEE/PMA0/Ch01.actual.CFD_RATE",
            "ft0_dcs:FEE/PMA0/Ch02.actual.CFD_RATE",
        ]
        aliases = ["alias_1", "alias_2"]

        # Act
        result_path = self.service._create_input_file(
            time_from, time_to, schema, elements, aliases
        )

        # Assert
        assert isinstance(result_path, Path)
        assert result_path.exists()
        assert result_path.suffix == ".csv"
        assert "darma_input_" in result_path.name

        # Check file content
        with open(result_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.strip().split("\n")
        assert len(lines) == 5  # timefrom, timeto, schema, element, alias

        assert lines[0].startswith("timefrom;01.07.2025;00:00:01.0")
        assert lines[1].startswith("timeto;02.07.2025;23:59:59.0")
        assert lines[2].startswith("schema;FT0ARCH")
        assert lines[3].startswith(
            "element;ft0_dcs:FEE/PMA0/Ch01.actual.CFD_RATE;"
            "ft0_dcs:FEE/PMA0/Ch02.actual.CFD_RATE"
        )
        assert lines[4].startswith("alias;alias_1;alias_2")

        # Cleanup
        result_path.unlink()

    def test_create_input_file_with_aliases_none(self):
        """Test input file creation with aliases=None."""
        # Arrange
        time_from = datetime.datetime(2025, 7, 1, 0, 0, 1)
        time_to = datetime.datetime(2025, 7, 2, 23, 59, 59)
        schema = DarmaApiSchema.FT0ARCH
        elements = ["test_element"]
        aliases = None

        # Act
        result_path = self.service._create_input_file(
            time_from, time_to, schema, elements, aliases
        )

        # Assert
        with open(result_path, encoding="utf-8") as f:
            content = f.read()

        lines = content.strip().split("\n")
        assert len(lines) == 4  # timefrom, timeto, schema, element (no alias)

        assert "alias;" not in content

        # Cleanup
        result_path.unlink()

    def test_parse_multiple_responses_empty_list(self):
        """Test parsing multiple responses with empty list."""
        # Act
        result = self.service._parse_multiple_responses([])

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert list(result.columns) == ["timestamp", "value", "element_name"]

    def test_parse_multiple_responses_single_file(self):
        """Test parsing multiple responses with single file."""
        # Arrange
        csv_content = """date;time;element_name/alias;value
2025-07-01;00:00:01;test_element;123.45
2025-07-01;00:00:02;test_element2;67.89"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            temp_file_path = Path(f.name)

        # Act
        result = self.service._parse_multiple_responses([temp_file_path])

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ["timestamp", "value", "element_name"]
        assert result.iloc[0]["value"] == 123.45
        assert result.iloc[1]["value"] == 67.89

        # Cleanup
        temp_file_path.unlink()

    def test_parse_multiple_responses_multiple_files(self):
        """Test parsing multiple responses with multiple files."""
        # Arrange
        csv_content1 = """date;time;element_name/alias;value
2025-07-01;00:00:01;test_element;123.45"""

        csv_content2 = """date;time;element_name/alias;value
2025-07-01;00:00:02;test_element2;67.89"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f1:
            f1.write(csv_content1)
            temp_file_path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f2:
            f2.write(csv_content2)
            temp_file_path2 = Path(f2.name)

        # Act
        result = self.service._parse_multiple_responses(
            [temp_file_path1, temp_file_path2]
        )

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ["timestamp", "value", "element_name"]

        # Should be sorted by timestamp
        assert result.iloc[0]["timestamp"] == pd.Timestamp("2025-07-01 00:00:01")
        assert result.iloc[1]["timestamp"] == pd.Timestamp("2025-07-01 00:00:02")

        # Cleanup
        temp_file_path1.unlink()
        temp_file_path2.unlink()

    def test_parse_multiple_responses_with_empty_files(self):
        """Test parsing multiple responses with some empty files."""
        # Arrange
        csv_content1 = """date;time;element_name/alias;value
2025-07-01;00:00:01;test_element;123.45"""

        csv_content2 = """date;time;element_name/alias;value"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f1:
            f1.write(csv_content1)
            temp_file_path1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f2:
            f2.write(csv_content2)
            temp_file_path2 = Path(f2.name)

        # Act
        result = self.service._parse_multiple_responses(
            [temp_file_path1, temp_file_path2]
        )

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1  # Only data from first file
        assert result.iloc[0]["value"] == 123.45

        # Cleanup
        temp_file_path1.unlink()
        temp_file_path2.unlink()

    def test_parse_multiple_responses_with_nonexistent_files(self):
        """Test parsing multiple responses with some nonexistent files."""
        # Arrange
        csv_content = """date;time;element_name/alias;value
2025-07-01;00:00:01;test_element;123.45"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            f.write(csv_content)
            temp_file_path = Path(f.name)

        nonexistent_file = Path("/nonexistent/file.csv")

        # Act
        result = self.service._parse_multiple_responses(
            [temp_file_path, nonexistent_file]
        )

        # Assert
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1  # Only data from existing file
        assert result.iloc[0]["value"] == 123.45

        # Cleanup
        temp_file_path.unlink()

    @pytest.mark.local_only
    def test_call_da_batch_client_single_client(self):
        """Test calling DA_batch_client with single client ID."""
        # Arrange
        input_file = Path(tempfile.gettempdir()) / "test_input.csv"
        output_base = Path(tempfile.gettempdir()) / "test_output"

        # Create a dummy input file
        with open(input_file, "w") as f:
            f.write("test content")

        # Mock the DA_batch_client functions
        with patch(
            "ageing_analysis.services.darma_api_service.upload_file"
        ) as mock_upload, patch(
            "ageing_analysis.services.darma_api_service.get_result_file"
        ) as mock_get_result, patch(
            "ageing_analysis.services.darma_api_service.save_result_file"
        ) as mock_save:
            mock_upload.return_value = ["client_id_1"]
            mock_get_result.return_value = "base64_content"
            mock_save.return_value = None

            # Act
            result = self.service._call_da_batch_client(input_file, output_base)

            # Assert
            assert len(result) == 1
            assert result[0].name == "test_output.csv"
            mock_upload.assert_called_once_with(
                str(input_file), self.service.upload_url
            )
            mock_get_result.assert_called_once_with(
                "client_id_1", self.service.result_url
            )
            mock_save.assert_called_once_with("base64_content", str(result[0]))

        # Cleanup
        input_file.unlink()

    @pytest.mark.local_only
    def test_call_da_batch_client_multiple_clients(self):
        """Test calling DA_batch_client with multiple client IDs."""
        # Arrange
        input_file = Path(tempfile.gettempdir()) / "test_input.csv"
        output_base = Path(tempfile.gettempdir()) / "test_output"

        # Create a dummy input file
        with open(input_file, "w") as f:
            f.write("test content")

        # Mock the DA_batch_client functions
        with patch(
            "ageing_analysis.services.darma_api_service.upload_file"
        ) as mock_upload, patch(
            "ageing_analysis.services.darma_api_service.get_result_file"
        ) as mock_get_result, patch(
            "ageing_analysis.services.darma_api_service.save_result_file"
        ) as mock_save, patch(
            "ageing_analysis.services.darma_api_service.request_and_save_parsed_data"
        ) as mock_request_parsed:
            mock_upload.return_value = ["client_id_1", "client_id_2"]
            mock_get_result.side_effect = ["base64_content_1", "base64_content_2"]
            mock_save.return_value = None
            mock_request_parsed.return_value = None

            # Act
            result = self.service._call_da_batch_client(input_file, output_base)

            # Assert
            assert len(result) == 2
            assert result[0].name == "test_output_1.csv"
            assert result[1].name == "test_output_2.csv"

            # Check that parsed data was requested
            mock_request_parsed.assert_called_once()

        # Cleanup
        input_file.unlink()

    @pytest.mark.local_only
    def test_call_da_batch_client_no_client_ids(self):
        """Test calling DA_batch_client when no client IDs are returned."""
        # Arrange
        input_file = Path(tempfile.gettempdir()) / "test_input.csv"
        output_base = Path(tempfile.gettempdir()) / "test_output"

        # Create a dummy input file
        with open(input_file, "w") as f:
            f.write("test content")

        # Mock the DA_batch_client functions
        with patch(
            "ageing_analysis.services.darma_api_service.upload_file"
        ) as mock_upload:
            mock_upload.return_value = None

            # Act
            result = self.service._call_da_batch_client(input_file, output_base)

            # Assert
            assert len(result) == 0

        # Cleanup
        input_file.unlink()

    @pytest.mark.local_only
    def test_call_da_batch_client_exception_handling(self):
        """Test calling DA_batch_client with exception handling."""
        # Arrange
        input_file = Path(tempfile.gettempdir()) / "test_input.csv"
        output_base = Path(tempfile.gettempdir()) / "test_output"

        # Create a dummy input file
        with open(input_file, "w") as f:
            f.write("test content")

        # Mock the DA_batch_client functions to raise an exception
        with patch(
            "ageing_analysis.services.darma_api_service.upload_file"
        ) as mock_upload:
            mock_upload.side_effect = Exception("Network error")

            # Act
            result = self.service._call_da_batch_client(input_file, output_base)

            # Assert
            assert len(result) == 1
            assert result[0].name == "test_output.csv"
            assert result[0].exists()

        # Cleanup
        input_file.unlink()
        result[0].unlink()

    @pytest.mark.local_only
    def test_get_data_integration(self):
        """Test the complete get_data method integration."""
        # Arrange
        time_from = datetime.datetime(2025, 7, 1, 0, 0, 0)
        time_to = datetime.datetime(2025, 7, 2, 0, 0, 0)
        schema = DarmaApiSchema.FT0ARCH
        elements = ["test_element_1", "test_element_2"]
        aliases = ["alias_1", "alias_2"]

        # Mock the DA_batch_client functions
        with patch(
            "ageing_analysis.services.darma_api_service.upload_file"
        ) as mock_upload, patch(
            "ageing_analysis.services.darma_api_service.get_result_file"
        ) as mock_get_result, patch(
            "ageing_analysis.services.darma_api_service.save_result_file"
        ) as mock_save, patch(
            "ageing_analysis.services.darma_api_service.request_and_save_parsed_data"
        ) as mock_request_parsed:
            mock_upload.return_value = ["client_id_1", "client_id_2"]
            mock_get_result.side_effect = ["base64_content_1", "base64_content_2"]
            mock_save.return_value = None
            mock_request_parsed.return_value = None

            # Create temporary output files with test data
            def mock_save_side_effect(base64_content, file_path):
                # Create a file with test data
                csv_content = """date;time;element_name/alias;value
2025-07-01;00:00:01;test_element_1;123.45
2025-07-01;00:00:02;test_element_2;67.89"""
                Path(file_path).write_text(csv_content)

            mock_save.side_effect = mock_save_side_effect

            # Act
            result = self.service.get_data(
                time_from, time_to, schema, elements, aliases
            )

            # Assert
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 4  # 2 rows from each file
            assert list(result.columns) == ["timestamp", "value", "element_name"]

            # Check that the data is sorted by timestamp
            timestamps = result["timestamp"].tolist()
            assert timestamps == sorted(timestamps)

    @pytest.mark.local_only
    def test_get_data_without_aliases(self):
        """Test get_data method without aliases."""
        # Arrange
        time_from = datetime.datetime(2025, 7, 1, 0, 0, 0)
        time_to = datetime.datetime(2025, 7, 2, 0, 0, 0)
        schema = DarmaApiSchema.FT0ARCH
        elements = ["test_element"]

        # Mock the DA_batch_client functions
        with patch(
            "ageing_analysis.services.darma_api_service.upload_file"
        ) as mock_upload, patch(
            "ageing_analysis.services.darma_api_service.get_result_file"
        ) as mock_get_result, patch(
            "ageing_analysis.services.darma_api_service.save_result_file"
        ) as mock_save:
            mock_upload.return_value = ["client_id_1"]
            mock_get_result.return_value = "base64_content"
            mock_save.return_value = None

            # Create temporary output file with test data
            def mock_save_side_effect(base64_content, file_path):
                csv_content = """date;time;element_name/alias;value
2025-07-01;00:00:01;test_element;123.45"""
                Path(file_path).write_text(csv_content)

            mock_save.side_effect = mock_save_side_effect

            # Act
            result = self.service.get_data(time_from, time_to, schema, elements)

            # Assert
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1
            assert result.iloc[0]["value"] == 123.45
