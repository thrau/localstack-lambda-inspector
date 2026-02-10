import datetime

from localstack.services.lambda_.invocation.executor_endpoint import ExecutorEndpoint
from localstack.utils.patch import patch

from localstack_lambda_inspector import invocation_log


@patch(ExecutorEndpoint.invoke, pass_target=True)
def _invoke(fn, self, payload: dict[str, str]):
    timestamp = datetime.datetime.now(tz=datetime.UTC)

    # perform the invoke
    result = fn(self, payload)

    invocation_log.log_invocation(
        timestamp,
        payload["invoke-id"],
        payload["invoked-function-arn"],
        payload["payload"],
        result,
    )

    return result
