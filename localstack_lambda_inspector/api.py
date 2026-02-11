import json

from rolo import Request, route, Response

from localstack_lambda_inspector import invocation_log


def recursive_dict_parse(obj):
    if isinstance(obj, str):
        if obj.startswith("{"):
            try:
                new_obj = json.loads(obj)
            except ValueError:
                return obj
            return recursive_dict_parse(new_obj)

    if isinstance(obj, dict):
        for k, v in obj.items():
            obj[k] = recursive_dict_parse(v)
    elif isinstance(obj, list):
        obj = [recursive_dict_parse(item) for item in obj]

    return obj


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

                invocation["payload"] = recursive_dict_parse(invocation["payload"])
                invocation["result"]["payload"] = recursive_dict_parse(
                    invocation["result"]["payload"]
                )

        return Response.for_json({"invocations": doc})
