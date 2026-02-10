import os

import requests
import streamlit as st

# Set page configuration
st.set_page_config(page_title="Lambda Invocations Viewer", layout="wide")

st.title("AWS Lambda Invocations")

# Endpoint URL
DEFAULT_ENDPOINT_URL = (
    "http://localhost:4566/_extension/lambda-inspector/invocations?formatted=true"
)
ENDPOINT_URL = os.environ.get("LAMBDA_INSPECTOR_ENDPOINT_URL") or DEFAULT_ENDPOINT_URL


@st.cache_data
def fetch_invocations():
    try:
        response = requests.get(ENDPOINT_URL)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None


# Sidebar for filters and controls
st.sidebar.header("Filters & Controls")

# Fuzzy ARN Filter
arn_filter = st.sidebar.text_input("Filter by Lambda ARN (fuzzy)", "", key="arn_filter")

# Limit the number of invocations to show
max_invocations = st.sidebar.number_input(
    "Show last X invocations", min_value=1, value=20, step=1, key="max_invocations"
)

# Refresh button in sidebar
if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

data = fetch_invocations()

if data and "invocations" in data:
    invocations = data["invocations"]

    if not invocations:
        st.info("No lambda invocations found.")
    else:
        # Filtering logic
        filtered_invocations = []
        for invocation in invocations:
            # 1. ARN Fuzzy Filter
            function_arn = invocation.get("function_arn", "")
            if arn_filter.lower() not in function_arn.lower():
                continue

            filtered_invocations.append(invocation)

        if not filtered_invocations:
            st.info("No invocations match the current filters.")
        else:
            # Display limited filtered invocations in reverse chronological order (newest first)
            # Since the original list from LocalStack is usually chronological (oldest first),
            # we reverse it first to get the "last" (most recent) ones.
            display_list = list(reversed(filtered_invocations))[:max_invocations]

            st.write(
                f"Showing {len(display_list)} of {len(filtered_invocations)} filtered invocations (Total: {len(invocations)})"
            )

            for invocation in display_list:
                timestamp = invocation.get("timestamp", "N/A")
                request_id = invocation.get("request_id", "N/A")
                function_arn = invocation.get("function_arn", "N/A")
                # Extract a short function name from ARN for better display
                function_name = (
                    function_arn.split(":")[-1] if ":" in function_arn else function_arn
                )

                # Determine status icon based on is_error
                result = invocation.get("result", {})
                is_error = result.get("is_error", False)
                status_icon = "❌" if is_error else "✅"

                expander_label = (
                    f"{status_icon} | {timestamp} | {function_name} | {request_id}"
                )

                with st.expander(expander_label):
                    st.subheader("Request Payload")
                    st.json(invocation.get("payload", {}))

                    st.subheader("Result/Response")
                    # Create a copy of the result to avoid modifying the original data
                    response_data = result.copy()
                    logs = response_data.pop("logs", [])
                    st.json(response_data)

                    st.subheader("Log Output")
                    if logs:
                        st.code("\n".join(logs), language="text")
                    else:
                        st.info("No logs available for this invocation.")
else:
    st.warning(
        "Could not retrieve invocations data. Make sure LocalStack is running and the endpoint is accessible."
    )
