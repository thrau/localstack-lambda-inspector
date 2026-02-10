import datetime
import json
import logging

from localstack.extensions.api import Extension, http
from localstack.utils.patch import patch
from rolo import route, Request, Response

from localstack_lambda_inspector import invocation_log

LOG = logging.getLogger(__name__)


class Api:
    @route("/_extensions/lambda-inspector/invocations", methods=["GET"])
    def list_invocations(self, request: Request):
        invocations = invocation_log.get_invocations()

        if request.args.get("arn"):
            invocations = [i for i in invocations if i.function_arn == request.args.get("arn")]

        # serialize
        doc = [i.to_dict() for i in invocations]

        if request.args.get("formatted") in ["true", "1"]:
            for invocation in doc:
                # split logs into a more readable format
                invocation["result"]["logs"] = invocation["result"]["logs"].splitlines()

                # parse payloads for nicer displaying
                if invocation["payload"].startswith("{"):
                    invocation["payload"] = json.loads(invocation["payload"])
                if invocation["result"]["payload"].startswith("{"):
                    invocation["result"]["payload"] = json.loads(invocation["result"]["payload"])

        return Response.for_json({"invocations": doc})


class LocalstackLambdaInspector(Extension):
    name = "localstack-lambda-inspector"

    def on_platform_start(self):
        # patch lambda ExecutorEndpoint to log invocations
        from localstack.services.lambda_.invocation.executor_endpoint import ExecutorEndpoint

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

    def update_gateway_routes(self, router: http.Router[http.RouteHandler]):
        # add the API to the router
        router.add(Api())
