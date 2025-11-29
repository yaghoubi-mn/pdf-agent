from google.genai import types


retry = types.HttpRetryOptions(
    attempts=10,
    exp_base=2,
    initial_delay=2,
    http_status_codes=[429, 500, 503, 504]
)