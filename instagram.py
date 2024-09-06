import os
import boto3
import uuid
from flask import Flask, request, jsonify
from flasgger import Swagger
from botocore.exceptions import ClientError  # Add this import


# Set dummy credentials for LocalStack
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'

app = Flask(__name__)
swagger = Swagger(app)

localstack_host = os.getenv('LOCALSTACK_HOST', 'localhost')
localstack_url = f'http://{localstack_host}:4566'

# Initialize S3 and DynamoDB clients for LocalStack
s3 = boto3.client('s3', endpoint_url=localstack_url, region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', endpoint_url=localstack_url, region_name='us-east-1')

# Bucket and Table names
BUCKET_NAME = 'images-bucket'
TABLE_NAME = 'images_metadata'

# Ensure S3 bucket exists
try:
    s3.head_bucket(Bucket=BUCKET_NAME)
except ClientError:
    # If bucket doesn't exist, create it
    s3.create_bucket(Bucket=BUCKET_NAME)

# Check if DynamoDB table exists, if not create it
def create_dynamodb_table():
    existing_tables = dynamodb.meta.client.list_tables()['TableNames']
    if TABLE_NAME not in existing_tables:
        dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {'AttributeName': 'image_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'image_id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )

# Create table if it doesn't exist
create_dynamodb_table()

@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Upload an image with metadata fields.
    ---
    parameters:
      - in: formData
        name: image
        type: file
        required: true
        description: The image file to upload
      - in: formData
        name: user_id
        type: string
        required: true
        description: The user ID associated with the image
      - in: formData
        name: title
        type: string
        required: true
        description: The title of the image
      - in: formData
        name: description
        type: string
        required: true
        description: A short description of the image
    responses:
      200:
        description: Image uploaded successfully
      400:
        description: Bad Request if fields are missing
    """
    # Check if an image is provided
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    # Get other form fields
    user_id = request.form.get('user_id')
    title = request.form.get('title')
    description = request.form.get('description')

    # Validate that required fields are provided
    if not user_id or not title or not description:
        return jsonify({'error': 'Missing required fields'}), 400

    file = request.files['image']
    image_id = str(uuid.uuid4())
    file_name = f'{image_id}_{file.filename}'

    # Upload image to S3
    s3.upload_fileobj(file, BUCKET_NAME, file_name)

    # Store metadata in DynamoDB
    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item={
        'image_id': image_id,
        'file_name': file_name,
        'metadata': {
            'user_id': user_id,
            'title': title,
            'description': description
        }
    })

    return jsonify({'image_id': image_id, 'message': 'Image uploaded successfully'})



@app.route('/images', methods=['GET'])
def list_images():
    """
    List all images with optional filters.
    ---
    parameters:
      - name: user_id
        in: query
        type: string
        description: Filter by user ID
    responses:
      200:
        description: List of images
    """
    filters = request.args.to_dict()
    table = dynamodb.Table(TABLE_NAME)

    # Simple scan operation with optional filters
    scan_kwargs = {}
    if 'user_id' in filters:
        scan_kwargs['FilterExpression'] = 'metadata.user_id = :user_id'
        scan_kwargs['ExpressionAttributeValues'] = {':user_id': filters['user_id']}

    response = table.scan(**scan_kwargs)
    return jsonify(response['Items'])


@app.route('/image/<image_id>', methods=['GET'])
def view_image(image_id):
    """
    View or download an image.
    ---
    parameters:
      - name: image_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: URL of the image
    """
    table = dynamodb.Table(TABLE_NAME)
    response = table.get_item(Key={'image_id': image_id})
    if 'Item' not in response:
        return jsonify({'error': 'Image not found'}), 404

    file_name = response['Item']['file_name']

    # Generate a signed URL for S3 object
    url = s3.generate_presigned_url('get_object',
                                    Params={'Bucket': BUCKET_NAME, 'Key': file_name},
                                    ExpiresIn=3600)
    
    return jsonify({'image_url': url})


@app.route('/image/<image_id>', methods=['DELETE'])
def delete_image(image_id):
    """
    Delete an image.
    ---
    parameters:
      - name: image_id
        in: path
        type: string
        required: true
    responses:
      200:
        description: Image deleted successfully
    """
    table = dynamodb.Table(TABLE_NAME)
    response = table.get_item(Key={'image_id': image_id})
    if 'Item' not in response:
        return jsonify({'error': 'Image not found'}), 404

    file_name = response['Item']['file_name']

    # Delete from S3
    s3.delete_object(Bucket=BUCKET_NAME, Key=file_name)

    # Delete from DynamoDB
    table.delete_item(Key={'image_id': image_id})

    return jsonify({'message': 'Image deleted successfully'})


if __name__ == '__main__':
    app.run(port=5000)
