import os, json, boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("TABLE_NAME", "StudentRecords")
table = dynamodb.Table(TABLE_NAME)

def _resp(status, body=None):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        },
        "body": json.dumps(body) if body is not None else "",
    }

def lambda_handler(event, context):
    method = event.get("httpMethod", "GET")

    # CORS preflight
    if method == "OPTIONS":
        return _resp(200, {})

    try:
        if method == "POST":
            payload = json.loads(event.get("body") or "{}")
            if "student_id" not in payload:
                return _resp(400, {"error": "student_id is required"})
            table.put_item(Item=payload)
            return _resp(200, {"message": "Student record created", "student": payload})

        elif method == "GET":
            params = event.get("queryStringParameters") or {}
            sid = params.get("student_id")
            if not sid:
                return _resp(400, {"error": "student_id is required"})
            res = table.get_item(Key={"student_id": sid})
            item = res.get("Item")
            if not item:
                return _resp(404, {"error": "not found"})
            return _resp(200, item)

        elif method == "PUT":
            payload = json.loads(event.get("body") or "{}")
            sid = payload.get("student_id")
            if not sid:
                return _resp(400, {"error": "student_id is required"})
            expr, names, values = [], {}, {}
            for k, v in payload.items():
                if k == "student_id":
                    continue
                expr.append(f"#_{k} = :{k}")
                names[f"#_{k}"] = k
                values[f":{k}"] = v
            if not expr:
                return _resp(400, {"error": "no fields to update"})
            res = table.update_item(
                Key={"student_id": sid},
                UpdateExpression="SET " + ", ".join(expr),
                ExpressionAttributeNames=names,
                ExpressionAttributeValues=values,
                ReturnValues="ALL_NEW",
            )
            return _resp(200, {"message": "Student record updated", "student": res["Attributes"]})

        elif method == "DELETE":
            params = event.get("queryStringParameters") or {}
            sid = params.get("student_id")
            if not sid:
                return _resp(400, {"error": "student_id is required"})
            table.delete_item(Key={"student_id": sid})
            return _resp(200, {"message": f"Student {sid} deleted"})

        return _resp(405, {"error": "method not allowed"})
    except Exception as e:
        return _resp(500, {"error": str(e)})
