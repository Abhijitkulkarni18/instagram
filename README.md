# Instagram-like Image Upload Service

This is a simple image upload service built using Flask, LocalStack, and AWS services like S3 and DynamoDB. The service allows users to upload images along with metadata (user ID, title, description), and it stores the image in S3 and the metadata in DynamoDB. The service is designed to scale and is tested with `pytest`.

## Features
- Upload images with metadata (user ID, title, description).
- List all uploaded images with optional filtering by `user_id`.
- View or download an image via a presigned URL.
- Delete images and their associated metadata.
- Local development environment using LocalStack to emulate AWS services.

## Tech Stack
- **Flask**: Web framework for creating the API.
- **LocalStack**: Emulates AWS services (S3, DynamoDB) for local development.
- **boto3**: AWS SDK for Python to interact with S3 and DynamoDB.
- **pytest**: Testing framework for unit tests.
- **Swagger**: API documentation and testing interface.

---

## Project Setup

### Prerequisites
1. **Python 3.7+**: Ensure Python is installed.
2. **Docker**: For running LocalStack in a Docker container.
3. **pip**: Python's package installer.

### 1. Clone the Repository
```bash
git clone <repository-url>
cd instagram-like-app
```

### 2. Local setup

```bash

python3 -m venv myenv

source myenv/bin/activate

pip install -r requirements.txt

export FLASK_APP=instagram.py

flask run
```

### 3. Run Test Cases

```bash
pytest
```
