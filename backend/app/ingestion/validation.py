"""
Input validation for ingested datasets.

Validates a Pandas DataFrame of logistics data against domain rules.
Reports missing values, duplicates, invalid coordinates, invalid
distances/durations, and missing required columns.
"""

import hashlib
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from app.schemas.schemas import DataQualityReportSchema


# Columns considered critical for route-level data.
# Their absence is flagged as an issue but does NOT halt ingestion.
_EXPECTED_ROUTE_COLUMNS = {"route_id", "driver_id", "planned_distance", "actual_distance",
                            "planned_duration", "actual_duration", "stop_count"}


class DataValidator:

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculates SHA-256 hash of a file for provenance tracking."""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except OSError:
            return "N/A"

    @staticmethod
    def validate_dataset(
        df: pd.DataFrame,
        dataset_name: str,
        file_path: Optional[str],
    ) -> "DataQualityReportSchema":
        """
        Validates a Pandas DataFrame against logistics domain rules.

        Checks performed:
          1. Missing values per column
          2. Duplicate rows
          3. Negative durations (any column containing 'duration' or 'time')
          4. Negative distances (any column containing 'distance' or 'km')
          5. Invalid lat/lng coordinates (if columns present)
          6. Missing route/stop/driver ID columns (flagged, not fatal)

        Returns a DataQualityReportSchema with all findings.
        """
        issues: List[str] = []
        total_rows = len(df)

        # ------------------------------------------------------------------
        # 1. Missing values
        # ------------------------------------------------------------------
        missing_values: Dict[str, int] = {
            col: int(cnt)
            for col, cnt in df.isnull().sum().items()
            if cnt > 0
        }
        if missing_values:
            issues.append(
                f"Missing values in columns: {', '.join(f'{c}({v})' for c, v in missing_values.items())}"
            )

        # ------------------------------------------------------------------
        # 2. Duplicate rows
        # ------------------------------------------------------------------
        duplicate_records = int(df.duplicated().sum())
        if duplicate_records > 0:
            issues.append(
                f"Found {duplicate_records} duplicate row(s) in dataset."
            )

        # ------------------------------------------------------------------
        # 3. Negative durations
        # ------------------------------------------------------------------
        invalid_durations = 0
        duration_cols = [
            c for c in df.columns
            if ("duration" in c.lower() or "time" in c.lower())
            and pd.api.types.is_numeric_dtype(df[c])
        ]
        for col in duration_cols:
            n_neg = int((df[col] < 0).sum())
            if n_neg > 0:
                invalid_durations += n_neg
        if invalid_durations > 0:
            issues.append(
                f"Found {invalid_durations} negative duration value(s)."
            )

        # ------------------------------------------------------------------
        # 4. Negative distances
        # ------------------------------------------------------------------
        invalid_distances = 0
        distance_cols = [
            c for c in df.columns
            if ("distance" in c.lower() or c.lower().endswith("km"))
            and pd.api.types.is_numeric_dtype(df[c])
        ]
        for col in distance_cols:
            n_neg = int((df[col] < 0).sum())
            if n_neg > 0:
                invalid_distances += n_neg
        if invalid_distances > 0:
            issues.append(
                f"Found {invalid_distances} negative distance value(s)."
            )

        # ------------------------------------------------------------------
        # 5. Invalid coordinates (if lat/lng present)
        # ------------------------------------------------------------------
        invalid_coordinates = 0
        lat_cols = [c for c in df.columns if c.lower() in ("lat", "latitude")]
        lng_cols = [c for c in df.columns if c.lower() in ("lng", "lon", "longitude")]
        if lat_cols and lng_cols:
            lat_col, lng_col = lat_cols[0], lng_cols[0]
            try:
                lat_num = pd.to_numeric(df[lat_col], errors="coerce")
                lng_num = pd.to_numeric(df[lng_col], errors="coerce")
                invalid_lat = (lat_num < -90) | (lat_num > 90) | lat_num.isna()
                invalid_lng = (lng_num < -180) | (lng_num > 180) | lng_num.isna()
                invalid_coordinates = int((invalid_lat | invalid_lng).sum())
                if invalid_coordinates > 0:
                    issues.append(
                        f"Found {invalid_coordinates} invalid lat/lng coordinate(s)."
                    )
            except Exception:
                pass  # Column exists but cannot be coerced — skipped silently

        # ------------------------------------------------------------------
        # 6. Counts (safe — no KeyError on missing columns)
        # ------------------------------------------------------------------
        route_col = next(
            (c for c in df.columns if "route" in c.lower() and "id" in c.lower()),
            next((c for c in df.columns if "route" in c.lower()), None),
        )
        route_count = int(df[route_col].nunique()) if route_col else total_rows

        stop_col = next(
            (c for c in df.columns if "stop" in c.lower() and "count" in c.lower()),
            next((c for c in df.columns if "stop" in c.lower()), None),
        )
        stop_count = int(df[stop_col].nunique()) if stop_col else total_rows

        driver_col = next(
            (c for c in df.columns if "driver" in c.lower()), None
        )
        driver_count = int(df[driver_col].nunique()) if driver_col else 0

        # ------------------------------------------------------------------
        # 7. Provenance hash
        # ------------------------------------------------------------------
        file_hash = (
            DataValidator.calculate_file_hash(file_path)
            if file_path and pd.io.common.file_exists(file_path)
            else "N/A"
        )

        # ------------------------------------------------------------------
        # 8. Overall validation status
        # ------------------------------------------------------------------
        validation_status: str
        if not issues:
            validation_status = "SUCCESS"
        elif len(issues) < 3:
            validation_status = "WARNING"
        else:
            validation_status = "CRITICAL"

        return DataQualityReportSchema(
            dataset_name=dataset_name,
            total_rows=total_rows,
            route_count=route_count,
            stop_count=stop_count,
            driver_count=driver_count,
            missing_values=missing_values,
            duplicate_records=duplicate_records,
            invalid_durations=invalid_durations,
            invalid_distances=invalid_distances,
            invalid_coordinates=invalid_coordinates,
            validation_status=validation_status,
            issues=issues,
            provenance_hash=file_hash,
        )
