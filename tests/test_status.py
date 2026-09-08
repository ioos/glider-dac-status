import json
from datetime import datetime, timedelta, timezone

import pytest
from flask import jsonify

from app import app

from status.trajectories import (
    calculate_distance_km,
    filter_large_jumps,
)


@app.route("/api/deployments")
def deployments_mock():
    return jsonify(_generate_status_json())


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["DEBUG"] = False

    with app.test_client() as client:
        yield client


def test_index(client):
    response = client.get("/")

    assert response.status_code == 200


def test_deployments_api(client):
    response = client.get("/api/deployments")

    assert response.status_code == 200

    json_data = response.get_json()

    assert (
        json_data["results"][0]["name"]
        == "test-20200101T0000Z"
    )


def _generate_status_json(data_type="api_return"):
    dt_now = datetime.now(timezone.utc)
    dt_yesterday = dt_now - timedelta(days=1)

    status_dict = {
        "results": [
            {
                "name": "test-20200101T0000Z",
                "datasetID": "test-20200101T0000Z",
                "id": "5ddddddddddddddddddddddd",
                "attribution": "Test Dataset",
                "username": "test_user",
                "archive_safe": True,
                "checksum": "2385f68e7603c9d9aebb6c327353288a",
                "completed": True,
                "deployment_date": dt_now.timestamp(),
                "deployment_dir": "test/test-20200101T0000Z",
                "dac_url": (
                    "https://gliders.ioos.us/providers/deployment/"
                    "5ddddddddddddddddddddddd"
                ),
                "glider_name": "test",
                "east": 180.0,
                "west": -180.0,
                "north": 90.0,
                "south": -90.0,
                "start": dt_yesterday.timestamp(),
                "end": dt_now.timestamp(),
                "delayed_mode": False,
                "estimated_deploy_date": None,
                "estimated_deploy_location": None,
                "graph": (
                    "https://gliders.ioos.us/erddap/tabledap/"
                    "test-20200101T0000Z.graph"
                ),
                "fgdc": (
                    "https://gliders.ioos.us/erddap/metadata/fgdc/"
                    "xml/test-20200101T0000Z_fgdc.xml"
                ),
                "institution": "unit_test",
                "iso": (
                    "https://gliders.ioos.us/erddap/tabledap/"
                    "test-20200101T0000Z.iso19115"
                ),
                "latest_nc_file": "test_20200105T0000Z.nc",
                "meta": (
                    "https://gliders.ioos.us/erddap/info/"
                    "test-20200101T0000Z/index"
                ),
                "nc_file_last_update": dt_yesterday.timestamp(),
                "nc_files_count": 30,
                "operator": "test",
                "potential_invalid_files": [],
                "rss": "https://gliders.ioos.us/erdap/rss/test.rss",
                "status": None,
                "subset": (
                    "https://gliders.ioos.us/erdap/tabledap/"
                    "test-20200101T0000Z.subset"
                ),
                "summary": "Testing only dataset",
                "tds": (
                    "https://gliders.ioos.us/thredds/dodsC/catalog/"
                    "deployments/test/test-20200101T0000Z.subset"
                ),
                "ts0": dt_yesterday.isoformat(),
                "ts1": dt_now.isoformat(),
                "updated": dt_now.timestamp(),
                "wmo_id": None,
            }
        ]
    }

    if data_type == "api_return":
        status_dict["num_results"] = len(
            status_dict["results"]
        )

    elif data_type == "written_json":
        status_dict["meta"] = {
            "fetch_time": dt_now.strftime(
                "%b %d, %Y %H:%M Z"
            )
        }

    return status_dict


def test_calculate_distance_km():
    point_a = (-74.0060, 40.7128)
    point_b = (-73.9857, 40.7484)

    distance = calculate_distance_km(
        point_a,
        point_b,
    )

    assert 3.0 < distance < 5.0


def test_filter_large_jumps_removes_outlier():
    coords = [
        (-74.0060, 40.7128),
        (-73.9857, 40.7484),
        (-80.1918, 25.7617),
    ]

    times = [
        "2025-01-01T00:00:00Z",
        "2025-01-01T01:00:00Z",
        "2025-01-01T02:00:00Z",
    ]

    cleaned_coords, cleaned_times, removed = filter_large_jumps(
        coords,
        times,
        max_jump_km=200,
    )

    assert len(cleaned_coords) == 2
    assert len(cleaned_times) == 2
    assert len(removed) == 1
    assert removed[0]["index"] == 2