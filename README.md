# StudentRecords Serverless API (AWS Lambda + API Gateway + DynamoDB)

> **Assignment alignment:** Implements a CRUD API for student records using AWS Lambda, API Gateway, and DynamoDB; includes HTTP testing steps and screenshots section with placeholders; reflection included.

---

## Overview

A serverless web API that stores student records in Amazon DynamoDB, with a single Lambda function handling CRUD and Amazon API Gateway exposing `/students` endpoints.

**Region used in example:** `us-east-2` (Ohio).

---

## Architecture

- **Amazon API Gateway (REST):** Routes HTTP requests to Lambda.  
- **AWS Lambda (Python 3.12):** Handles `POST`, `GET`, `PUT`, `DELETE`. Uses proxy integration.  
- **Amazon DynamoDB:** Table `StudentRecords` with partition key `student_id (String)`.  
- **IAM Role:** Lambda execution role with CloudWatch Logs + DynamoDB access.

```
Client (curl/Postman/Browser)
        │
        ▼
API Gateway (REST /students)
        │   (Lambda proxy integration)
        ▼
Lambda: StudentRecordHandler
        │   (boto3)
        ▼
DynamoDB: StudentRecords
```

---

## Prerequisites

- AWS account + console access.
- Python 3.12 runtime for Lambda.
- Basic terminal.

---

## Resources to Create

1. **DynamoDB** → Table `StudentRecords`  
   - Partition key: `student_id (String)`  
   - Capacity mode: **On-demand**

2. **IAM Role** for Lambda (e.g., `StudentRecordRole`)  
   - Policies:
     - `AWSLambdaBasicExecutionRole`
     - `AmazonDynamoDBFullAccess` 

3. **Lambda** → Function `StudentRecordHandler` (Python 3.12)  
   - Environment variable: `TABLE_NAME=StudentRecords`  
   - Attach the IAM role from step 2.

4. **API Gateway (REST)** → API `StudentAPI`  
   - Resource: `/students`  
   - Methods (proxy integration **ON**): **POST**, **GET**, **PUT**, **DELETE**  
   - CORS: Enable on `/students` to add `OPTIONS (Mock)`  
   - Deploy to stage, e.g., `dev` → **Invoke URL**: `https://hlay7s20ee.execute-api.us-east-2.amazonaws.com/dev`

---

## Lambda Code (Python)

> Save as `lambda_function.py` in the Lambda console editor (or deploy via zip).

```python
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
```

---

## Endpoints

Base URL: `https://hlay7s20ee.execute-api.us-east-2.amazonaws.com/dev` 

- `POST /students` – create a record (body contains `student_id` and other fields)
- `GET /students?student_id=<id>` – read a record
- `PUT /students` – update fields (body includes `student_id` + fields to change)
- `DELETE /students?student_id=<id>` – delete a record

---

## Test Commands (single line)

Replace `https://hlay7s20ee.execute-api.us-east-2.amazonaws.com/dev` with your stage URL.

**Create**
```bash
curl -i -X POST "https://hlay7s20ee.execute-api.us-east-2.amazonaws.com/dev/students" -H "Content-Type: application/json" -d '{"student_id":"123","name":"John Doe","course":"Enterprise Software"}'
```

**Read**
```bash
curl -i "https://hlay7s20ee.execute-api.us-east-2.amazonaws.com/dev/students?student_id=123"
```

**Update**
```bash
curl -i -X PUT "https://hlay7s20ee.execute-api.us-east-2.amazonaws.com/dev/students" -H "Content-Type: application/json" -d '{"student_id":"123","email":"john@example.edu","course":"Cloud Architecture"}'
```

**Delete**
```bash
curl -i -X DELETE "https://hlay7s20ee.execute-api.us-east-2.amazonaws.com/dev/students?student_id=123"
```

---

## Screenshots (using your files)

Place images in `docs/images/` inside this repo. I pre-filled links below and noted which local files to rename from your set.

1. **API Gateway – Resources & Methods ( `/students` )**  
   - **Expected path in repo:** `docs/images/api-gateway-resources.png`  
   - **Rename from your file:** `Screenshot 2025-09-17 at 9.18.31 PM.png`  
   ![API Gateway Resources](docs/images/api-gateway-resources.png)

2. **API Gateway – Stage with Invoke URL**  
   - **Expected path in repo:** `docs/images/api-gateway-stage.png`  
   - **Rename from your file:** `Screenshot 2025-09-17 at 8.08.51 PM.png`  
   ![API Gateway Stage](docs/images/api-gateway-stage.png)

3. **Terminal – POST success**  
   - **Expected path in repo:** `docs/images/curl-post.png`  
   - **Rename from your file:** `Screenshot 2025-09-17 at 9.12.35 PM.png`  
   ![curl POST](docs/images/curl-post.png)

4. **Terminal – GET success**  
   - **Expected path in repo:** `docs/images/curl-get.png`  
   - **Rename from your file:** `Screenshot 2025-09-17 at 9.06.54 PM.png` (or your clean GET-only shot)  
   ![curl GET](docs/images/curl-get.png)

5. **DynamoDB – Explore items showing sample record**  
   - **Expected path in repo:** `docs/images/dynamodb-item.png`  
   - **Rename from your file:** `Screenshot 2025-09-17 at 9.13.28 PM.png`  
   ![DynamoDB item](docs/images/dynamodb-item.png)


## Troubleshooting

- **Missing items in DynamoDB** → Ensure `TABLE_NAME=StudentRecords` env var is set and region matches.  
- **`{"error":"student_id is required"}`** → Your request body or query string is missing `student_id`.  
- **CORS errors from browser** → Re-run **Enable CORS** on `/students` and redeploy; keep `OPTIONS (Mock)` method.  
- **Proxy integration** → Each CRUD method must show **Lambda proxy integration: True**.

---

## Cleanup (avoid costs)

- API Gateway: delete stage & API.  
- Lambda: delete the function.  
- CloudWatch Logs: delete log group `/aws/lambda/StudentRecordHandler` (optional).  
- DynamoDB: delete `StudentRecords`.  
- IAM: remove or delete the dedicated role if unused.

---

## Reflection

### What I built
A serverless CRUD API using AWS managed services: API Gateway, Lambda, and DynamoDB. The design favors simplicity, stateless compute, and pay-per-use storage—perfect for spiky classroom workloads.

### Core learning opportunities
- **Service wiring & event flow:** Understanding how API Gateway’s **Lambda proxy integration** shapes the `event` and why the function must parse `httpMethod`, `queryStringParameters`, and `body`.
- **Data modeling in DynamoDB:** Choosing a single-partition key (`student_id`) is enough for CRUD; recognizes how access patterns drive table design.
- **CORS in practice:** Distinguishing **preflight (`OPTIONS`)** from actual requests, and why API Gateway’s **Mock OPTIONS** plus Lambda’s headers make browser calls succeed.
- **Consistency across regions:** All resources must live in the same region; otherwise APIs call the wrong function or tables appear empty.
- **Least-privilege thinking:** Starting with broad DynamoDB permissions is convenient for learning; next step is scoping to `StudentRecords` only.
- **Operational visibility:** CloudWatch logs (via `AWSLambdaBasicExecutionRole`) are essential for debugging payload shape mismatches and exceptions.

### Challenges & fixes
- **Multiline curl dropped bodies** → Use **single-line** commands so JSON reaches Lambda.  
- **“Method not allowed”** → Returned `405` for unexpected verbs—helps validate routing.  
- **Item not found** → Good reminder to return clear `404` vs. `200` with empty bodies.

### What I’d improve next
- **Input validation** with JSON schema or Pydantic.  
- **Error handling** patterns with structured error objects.  
- **Auth** via API keys or Cognito for protected endpoints.  
- **IaC** with AWS SAM/Terraform to make builds reproducible.  
- **Automated tests** (pytest) that hit a **local DynamoDB** or use moto for unit tests.

---

## License

Educational use.
