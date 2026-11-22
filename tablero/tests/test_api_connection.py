"""Exercise the dashboard's HTTP prediction contract."""

import json
import os
import unittest
from unittest.mock import patch

import requests

from tablero import api_connection
from common.profiles import DEFAULT_PROFILE, ValidationError


def _response(status: int, body: object) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body).encode("utf-8")
    return response


def _prediction(rank: int | None) -> dict[str, object]:
    return {
        "probability_yes": 0.25,
        "probability_no": 0.75,
        "prediction": "yes",
        "rank": rank,
    }


class PredictionConnectionTests(unittest.TestCase):
    @patch("tablero.api_connection.requests.post")
    def test_single_posts_without_rank(self, post):
        post.return_value = _response(200, {"predictions": [_prediction(None)]})
        with patch.dict(os.environ, clear=True):
            result = api_connection.predict_one(DEFAULT_PROFILE)

        self.assertEqual(post.call_args.args, ("http://localhost:8001/api/v1/predict",))
        self.assertEqual(post.call_args.kwargs["json"], {
            "inputs": [DEFAULT_PROFILE],
            "include_rank": False,
        })
        self.assertIsNone(result.rank)
        self.assertEqual(result.probability_yes, 0.25)

    @patch("tablero.api_connection.requests.post")
    def test_batch_uses_configured_endpoint_and_keeps_input_order(self, post):
        inputs = [DEFAULT_PROFILE, {**DEFAULT_PROFILE, "age": 55}]
        post.return_value = _response(200, {"predictions": [_prediction(2), _prediction(1)]})
        with patch.dict(os.environ, {"API_URL": "api", "API_PORT": "9000"}):
            result = api_connection.predict_many(inputs)

        post.assert_called_once()
        self.assertEqual(post.call_args.args, ("http://api:9000/api/v1/predict",))
        self.assertEqual(post.call_args.kwargs["json"], {"inputs": inputs, "include_rank": True})
        self.assertEqual([row.rank for row in result], [2, 1])

    @patch("tablero.api_connection.requests.post")
    def test_empty_batch_skips_http(self, post):
        self.assertEqual(api_connection.predict_many([]), [])
        post.assert_not_called()

    @patch("tablero.api_connection.requests.post")
    def test_validation_errors_reach_dashboard(self, post):
        post.return_value = _response(422, {"detail": [{"msg": "Age is required"}]})
        with self.assertRaisesRegex(ValidationError, "Age is required"):
            api_connection.predict_one({})

    @patch("tablero.api_connection.requests.post")
    def test_api_failures_reach_dashboard(self, post):
        post.side_effect = requests.exceptions.Timeout
        with self.assertRaisesRegex(api_connection.ModelUnavailableError, "timed out"):
            api_connection.predict_one(DEFAULT_PROFILE)

        post.side_effect = None
        post.return_value = _response(503, {"detail": "Model unavailable"})
        with self.assertRaisesRegex(api_connection.ModelUnavailableError, "HTTP 503"):
            api_connection.predict_one(DEFAULT_PROFILE)

    @patch("tablero.api_connection.requests.post")
    def test_incomplete_or_invalid_results_are_rejected(self, post):
        post.return_value = _response(200, {"predictions": []})
        with self.assertRaisesRegex(api_connection.ModelUnavailableError, "number of results"):
            api_connection.predict_many([DEFAULT_PROFILE])

        post.return_value = _response(200, {"predictions": [_prediction(-1)]})
        with self.assertRaisesRegex(api_connection.ModelUnavailableError, "invalid response"):
            api_connection.predict_many([DEFAULT_PROFILE])
