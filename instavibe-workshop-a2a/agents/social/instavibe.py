# spanner_data_fetchers.py

import os
from dotenv import load_dotenv
import traceback
from datetime import datetime, timezone
import json # For example usage printing

from google.cloud import spanner
from google.cloud.spanner_v1 import param_types
from google.api_core import exceptions

load_dotenv()
# --- Spanner Configuration ---
INSTANCE_ID = os.environ.get("SPANNER_INSTANCE_ID", "instavibe-graph-instance")
DATABASE_ID = os.environ.get("SPANNER_DATABASE_ID", "graphdb")
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")

if not PROJECT_ID:
    print("Warning: GOOGLE_CLOUD_PROJECT environment variable not set.")

# --- Spanner Client Initialization ---
db_instance = None
spanner_client = None
try:
    if PROJECT_ID:
        spanner_client = spanner.Client(project=PROJECT_ID)
        instance = spanner_client.instance(INSTANCE_ID)
        database = instance.database(DATABASE_ID)
        print(f"Attempting to connect to Spanner: {instance.name}/databases/{database.name}")

        if not database.exists():
             print(f"Error: Database '{database.name}' does not exist in instance '{instance.name}'.")
             db_instance = None
        else:
            print("Spanner database connection check successful.")
            db_instance = database
    else:
        print("Skipping Spanner client initialization due to missing GOOGLE_CLOUD_PROJECT.")

except exceptions.NotFound:
    print(f"Error: Spanner instance '{INSTANCE_ID}' not found in project '{PROJECT_ID}'.")
    db_instance = None
except Exception as e:
    print(f"An unexpected error occurred during Spanner initialization: {e}")
    db_instance = None

def run_sql_query(sql, params=None, param_types=None, expected_fields=None):
    """
    Executes a standard SQL query against the Spanner database.
    Returns: list[dict] or None on error.
    """
    if not db_instance:
        print("Error: Database connection is not available.")
        return None

    results_list = []
    print(f"--- Executing SQL Query ---")
    # print(f"SQL: {sql}")

    try:
        with db_instance.snapshot() as snapshot:
            results = snapshot.execute_sql(
                sql,
                params=params,
                param_types=param_types
            )

            field_names = expected_fields
            if not field_names:
                 print("Error: expected_fields must be provided to run_sql_query.")
                 return None

            for row in results:
                if len(field_names) != len(row):
                     print(f"Warning: Mismatch between field names ({len(field_names)}) and row values ({len(row)}). Skipping row: {row}")
                     continue
                results_list.append(dict(zip(field_names, row)))

    except (exceptions.NotFound, exceptions.PermissionDenied, exceptions.InvalidArgument) as spanner_err:
        print(f"Spanner SQL Query Error ({type(spanner_err).__name__}): {spanner_err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during SQL query execution or processing: {e}")
        traceback.print_exc()
        return None

    return results_list


def run_graph_query( graph_sql, params=None, param_types=None, expected_fields=None):
    """
    Executes a Spanner Graph Query (GQL).
    Returns: list[dict] or None on error.
    """
    if not db_instance:
        print("Error: Database connection is not available.")
        return None

    results_list = []
    print(f"--- Executing Graph Query ---")
    # print(f"GQL: {graph_sql}") # Uncomment for verbose query logging

    try:
        with db_instance.snapshot() as snapshot:
            results = snapshot.execute_sql(
                graph_sql,
                params=params,
                param_types=param_types
            )

            field_names = expected_fields
            if not field_names:
                 print("Error: expected_fields must be provided to run_graph_query.")
                 return None

            for row in results:
                if len(field_names) != len(row):
                     print(f"Warning: Mismatch between field names ({len(field_names)}) and row values ({len(row)}). Skipping row: {row}")
                     continue
                results_list.append(dict(zip(field_names, row)))

    except (exceptions.NotFound, exceptions.PermissionDenied, exceptions.InvalidArgument) as spanner_err:
        print(f"Spanner Graph Query Error ({type(spanner_err).__name__}): {spanner_err}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during graph query execution or processing: {e}")
        traceback.print_exc()
        return None

    return results_list
