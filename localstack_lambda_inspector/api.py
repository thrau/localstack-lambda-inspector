import json

from rolo import Request, route, Response

from localstack_lambda_inspector import invocation_log


class Api:
    @route("/_extension/lambda-inspector/invocations", methods=["GET"])
    def list_invocations(self, request: Request):

        invocations = invocation_log.get_invocations()

        if request.args.get("arn"):
            invocations = [
                i for i in invocations if i.function_arn == request.args.get("arn")
            ]

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
                    invocation["result"]["payload"] = json.loads(
                        invocation["result"]["payload"]
                    )

        return Response.for_json({"invocations": doc})
