import csv
import io
import math
from pathlib import Path

from connection import get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STAGING_DIR = PROJECT_ROOT / "data" / "staging"

DATASETS = [
    ("collisions_cleaned.csv", "cleaned.collisions"),
    ("vehicles_cleaned.csv", "cleaned.vehicles"),
    ("casualties_cleaned.csv", "cleaned.casualties"),
]

# Reverse mappings from src/transformation/standardize.py.
# Values must match that file exactly; unknown labels fail before COPY.
CATEGORY_MAPPINGS = {
    "collision_severity": {
        "Fatal": "1", "Serious": "2", "Slight": "3",
    },
    "road_type": {
        "Roundabout": "1",
        "One way street": "2",
        "Dual carriageway": "3",
        "Single carriageway": "6",
        "Slip road": "7",
        "Unknown": "9",
        "One way street/Slip road": "12",
    },
    "light_conditions": {
        "Daylight": "1",
        "Darkness - lights lit": "4",
        "Darkness - lights unlit": "5",
        "Darkness - lightsunlit": "5",
        "Darkness - no lighting": "6",
        "Darkness - lighting unknown": "7",
    },
    "weather_conditions": {
        "Fine no high winds": "1",
        "Raining no high winds": "2",
        "Snowing no high winds": "3",
        "Fine + high winds": "4",
        "Raining + high winds": "5",
        "Snowing + high winds": "6",
        "Fog or mist": "7",
        "Other": "8",
        "Unknown": "9",
    },
    "road_surface_conditions": {
        "Dry": "1",
        "Wet or damp": "2",
        "Snow": "3",
        "Frost or ice": "4",
        "Flood over 3cm deep": "5",
        "Oil or diesel": "6",
        "Mud": "7",
        "Unknown": "9",
    },
    "urban_or_rural_area": {
        "Urban": "1", "Rural": "2", "Unallocated": "3",
    },
    "vehicle_type": {
        "Pedal cycle": "1",
        "Motorcycle 50cc and under": "2",
        "Motorcycle 125cc and under": "3",
        "Motorcycle over 125cc and up to 500cc": "4",
        "Motorcycle over 500cc": "5",
        "Taxi/Private hire car": "8",
        "Car": "9",
        "Minibus (8 - 16 passenger seats)": "10",
        "Bus or coach (17 or more pass seats)": "11",
        "Ridden horse": "16",
        "Agricultural vehicle": "17",
        "Tram": "18",
        "Van / Goods 3.5 tonnes mgw or under": "19",
        "Goods over 3.5t. and under 7.5t": "20",
        "Goods 7.5 tonnes mgw and over": "21",
        "Mobility scooter": "22",
        "Electric motorcycle": "23",
        "Other vehicle": "90",
        "Motorcycle - unknown cc": "97",
        "Goods vehicle - unknown weight": "98",
        "Unknown vehicle type (self rep only)": "99",
        "Motorcycle - Scooter (1979-1998)": "103",
        "Motorcycle (1979-1998)": "104",
        "Motorcycle - Combination (1979-1998)": "105",
        "Motorcycle over 125cc (1999-2004)": "106",
        "Taxi (excluding private hire cars) (1979-2004)": "108",
        "Car (including private hire cars) (1979-2004)": "109",
        "Minibus/Motor caravan (1979-1998)": "110",
        "Goods over 3.5 tonnes (1979-1998)": "113",
    },
    "sex_of_driver": {"Male": "1", "Female": "2", "Not known": "3"},
    "age_band_of_driver": {
        "0 - 5": "1", "6 - 10": "2", "11 - 15": "3",
        "16 - 20": "4", "21 - 25": "5", "26 - 35": "6",
        "36 - 45": "7", "46 - 55": "8", "56 - 65": "9",
        "66 - 75": "10", "Over 75": "11",
    },
    "propulsion_code": {
        "Petrol": "1", "Heavy oil": "2", "Electric": "3",
        "Steam": "4", "Gas": "5", "Petrol/Gas (LPG)": "6",
        "Gas/Bi-fuel": "7", "Hybrid electric": "8",
        "Gas Diesel": "9", "New fuel technology": "10",
        "Fuel cells": "11", "Electric diesel": "12",
    },
    "casualty_class": {
        "Driver or rider": "1", "Passenger": "2", "Pedestrian": "3",
    },
    "sex_of_casualty": {
        "Male": "1", "Female": "2", "unknown (self reported)": "9",
    },
    "age_band_of_casualty": {
        "0 - 5": "1", "6 - 10": "2", "11 - 15": "3",
        "16 - 20": "4", "21 - 25": "5", "26 - 35": "6",
        "36 - 45": "7", "46 - 55": "8", "56 - 65": "9",
        "66 - 75": "10", "66 -75": "10", "Over 75": "11",
    },
    "casualty_severity": {"Fatal": "1", "Serious": "2", "Slight": "3"},
    "casualty_type": {
        "Pedestrian": "0",
        "Cyclist": "1",
        "Motorcycle 50cc and under rider or passenger": "2",
        "Motorcycle 125cc and under rider or passenger": "3",
        "Motorcycle over 125cc and up to 500cc rider or passenger": "4",
        "Motorcycle over 500cc rider or passenger": "5",
        "Taxi/Private hire car occupant": "8",
        "Car occupant": "9",
        "Minibus (8 - 16 passenger seats) occupant": "10",
        "Bus or coach occupant (17 or more pass seats)": "11",
        "Horse rider": "16",
        "Agricultural vehicle occupant": "17",
        "Tram occupant": "18",
        "Van / Goods vehicle (3.5 tonnes mgw or under) occupant": "19",
        "Goods vehicle (over 3.5t. and under 7.5t.) occupant": "20",
        "Goods vehicle (7.5 tonnes mgw and over) occupant": "21",
        "Mobility scooter rider": "22",
        "Electric motorcycle rider or passenger": "23",
        "Other vehicle occupant": "90",
        "Motorcycle - unknown cc rider or passenger": "97",
        "Goods vehicle (unknown weight) occupant": "98",
        "Unknown vehicle type (self rep only)": "99",
        "Motorcycle - Scooter (1979-1998)": "103",
        "Motorcycle (1979-1998)": "104",
        "Motorcycle - Combination (1979-1998)": "105",
        "Motorcycle over 125cc (1999-2004)": "106",
        "Taxi (excluding private hire cars) (1979-2004)": "108",
        "Car (including private hire cars) (1979-2004)": "109",
        "Minibus/Motor caravan (1979-1998)": "110",
        "Goods over 3.5 tonnes (1979-1998)": "113",
    },
}

INTEGER_COLUMNS = {
    "collision_year", "police_force", "collision_severity",
    "number_of_vehicles", "number_of_casualties", "day_of_week",
    "local_authority_district", "first_road_class", "first_road_number",
    "road_type", "speed_limit", "junction_detail_historic",
    "junction_detail", "junction_control", "second_road_class",
    "second_road_number", "pedestrian_crossing_human_control_historic",
    "pedestrian_crossing_physical_facilities_historic", "pedestrian_crossing",
    "light_conditions", "weather_conditions", "road_surface_conditions",
    "special_conditions_at_site", "carriageway_hazards_historic",
    "carriageway_hazards", "urban_or_rural_area",
    "did_police_officer_attend_scene_of_accident", "trunk_road_flag",
    "enhanced_severity_collision", "collision_injury_based",
    "vehicle_reference", "vehicle_type", "towing_and_articulation",
    "vehicle_manoeuvre_historic", "vehicle_manoeuvre",
    "vehicle_direction_from", "vehicle_direction_to",
    "vehicle_location_restricted_lane_historic",
    "vehicle_location_restricted_lane", "junction_location",
    "skidding_and_overturning", "hit_object_in_carriageway",
    "vehicle_leaving_carriageway", "hit_object_off_carriageway",
    "first_point_of_impact", "vehicle_left_hand_drive",
    "journey_purpose_of_driver_historic", "journey_purpose_of_driver",
    "sex_of_driver", "age_of_driver", "age_band_of_driver",
    "engine_capacity_cc", "propulsion_code", "age_of_vehicle",
    "driver_imd_decile", "escooter_flag", "driver_distance_banding",
    "casualty_reference", "casualty_class", "sex_of_casualty",
    "age_of_casualty", "age_band_of_casualty", "casualty_severity",
    "pedestrian_location", "pedestrian_movement", "car_passenger",
    "bus_or_coach_passenger", "pedestrian_road_maintenance_worker",
    "casualty_type", "casualty_imd_decile", "enhanced_casualty_severity",
    "casualty_injury_based", "casualty_distance_banding",
}

FLOAT_COLUMNS = {
    "location_easting_osgr", "location_northing_osgr", "longitude", "latitude",
    "collision_adjusted_severity_serious", "collision_adjusted_severity_slight",
    "casualty_adjusted_severity_serious", "casualty_adjusted_severity_slight",
}

def convert_value(column, raw_value, table_name, row_number):
    value = raw_value.strip()

    if value == "":
        return r"\N"

    if column in CATEGORY_MAPPINGS:
        mapping = CATEGORY_MAPPINGS[column]
        if value in mapping:
            return mapping[value]
        # Also allow original numeric category codes in case a CSV has not
        # been label-standardized.
        try:
            numeric = int(float(value))
        except ValueError:
            raise ValueError(
                f"Unknown category {value!r} in {table_name}.{column}, "
                f"CSV row {row_number}"
            )
        return str(numeric)

    if column in INTEGER_COLUMNS:
        try:
            numeric = float(value)
        except ValueError:
            raise ValueError(
                f"Expected integer-like value {value!r} in "
                f"{table_name}.{column}, CSV row {row_number}"
            )
        if not math.isfinite(numeric) or not numeric.is_integer():
            raise ValueError(
                f"Expected integer-like value {value!r} in "
                f"{table_name}.{column}, CSV row {row_number}"
            )
        return str(int(numeric))

    if column in FLOAT_COLUMNS:
        try:
            numeric = float(value)
        except ValueError:
            raise ValueError(
                f"Expected numeric value {value!r} in "
                f"{table_name}.{column}, CSV row {row_number}"
            )
        if not math.isfinite(numeric):
            raise ValueError(
                f"Expected finite numeric value {value!r} in "
                f"{table_name}.{column}, CSV row {row_number}"
            )
        return repr(numeric)

    return value


def load_csv(cursor, csv_path, table_name):
    """Validate and bulk-load a cleaned CSV into an existing PostgreSQL table."""

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        columns = next(reader, None)

        if not columns:
            raise ValueError(f"CSV is empty or has no header: {csv_path.name}")
        if len(columns) != len(set(columns)):
            raise ValueError(f"Duplicate CSV headers: {csv_path.name}")

        schema_name, relation_name = table_name.split(".", 1)
        cursor.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            (schema_name, relation_name),
        )
        db_metadata = cursor.fetchall()
        db_columns = [row[0] for row in db_metadata]
        db_types = {row[0]: row[1] for row in db_metadata}

        if not db_columns:
            raise ValueError(f"Database table does not exist: {table_name}")

        missing = set(db_columns) - set(columns)
        extra = set(columns) - set(db_columns)
        if missing or extra:
            raise ValueError(
                f"Schema mismatch for {table_name}. "
                f"Missing: {sorted(missing)}; extra: {sorted(extra)}"
            )

        positions = [columns.index(column) for column in db_columns]
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(db_columns)

        row_count = 0
        for row in reader:
            csv_row_number = row_count + 2
            if len(row) != len(columns):
                raise ValueError(
                    f"Malformed row {csv_row_number} in {csv_path.name}"
                )

            reordered = [row[index] for index in positions]
            converted = [
                convert_value(column, raw_value, table_name, csv_row_number)
                for column, raw_value in zip(db_columns, reordered)
            ]
            writer.writerow(converted)
            row_count += 1

        buffer.seek(0)
        cursor.copy_expert(
            f"COPY {table_name} ({', '.join(db_columns)}) "
            r"FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '\N')",
            buffer,
        )

        return row_count


def main():
    connection = None
    try:
        connection = get_connection()

        # All tables load in one transaction; a failure rolls back the entire load.
        with connection:
            with connection.cursor() as cursor:
                for filename, table_name in DATASETS:
                    csv_path = STAGING_DIR / filename
                    if not csv_path.is_file():
                        raise FileNotFoundError(csv_path)

                    print(f"Loading {filename} into {table_name}...")
                    count = load_csv(cursor, csv_path, table_name)
                    print(f"  Copied {count:,} rows.")

                print("\nVerifying database row counts:")
                for _, table_name in DATASETS:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    print(f"  {table_name}: {cursor.fetchone()[0]:,}")

        print("\nDatabase load completed successfully.")
    except Exception as error:
        print(f"\nDatabase load failed: {error}")
        print("The transaction has been rolled back.")
        raise
    finally:
        if connection is not None:
            connection.close()


if __name__ == "__main__":
    main()
