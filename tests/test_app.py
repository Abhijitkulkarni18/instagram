import pytest
from instagram import app
from io import BytesIO

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

### Test Cases for the Upload Image API

def test_upload_image_success(client):
    """Test successful image upload with valid form data"""
    data = {
        'user_id': '12345',
        'title': 'Test Image',
        'description': 'This is a test image.'
    }
    response = client.post('/upload', data={
        'image': (BytesIO(b'fake image data'), 'test_image.jpg'),
        'user_id': data['user_id'],
        'title': data['title'],
        'description': data['description']
    })
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'image_id' in json_data
    assert json_data['message'] == 'Image uploaded successfully'


def test_upload_image_missing_image(client):
    """Test image upload with missing image file"""
    data = {
        'user_id': '12345',
        'title': 'Test Image',
        'description': 'This is a test image.'
    }
    response = client.post('/upload', data={
        'user_id': data['user_id'],
        'title': data['title'],
        'description': data['description']
    })
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'No image provided'


def test_upload_image_missing_user_id(client):
    """Test image upload with missing user_id"""
    data = {
        'title': 'Test Image',
        'description': 'This is a test image.'
    }
    response = client.post('/upload', data={
        'image': (BytesIO(b'fake image data'), 'test_image.jpg'),
        'title': data['title'],
        'description': data['description']
    })
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'Missing required fields'


def test_upload_image_missing_title(client):
    """Test image upload with missing title"""
    data = {
        'user_id': '12345',
        'description': 'This is a test image.'
    }
    response = client.post('/upload', data={
        'image': (BytesIO(b'fake image data'), 'test_image.jpg'),
        'user_id': data['user_id'],
        'description': data['description']
    })
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'Missing required fields'


def test_upload_image_missing_description(client):
    """Test image upload with missing description"""
    data = {
        'user_id': '12345',
        'title': 'Test Image'
    }
    response = client.post('/upload', data={
        'image': (BytesIO(b'fake image data'), 'test_image.jpg'),
        'user_id': data['user_id'],
        'title': data['title']
    })
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'Missing required fields'


def test_upload_image_empty_fields(client):
    """Test image upload with empty fields"""
    response = client.post('/upload', data={
        'image': (BytesIO(b'fake image data'), 'test_image.jpg'),
        'user_id': '',
        'title': '',
        'description': ''
    })
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'Missing required fields'


### Test Cases for the List Images API

def test_list_images_no_filters(client):
    """Test listing images without any filters"""
    response = client.get('/images')
    assert response.status_code == 200
    assert isinstance(response.get_json(), list)  # Expecting a list of images


def test_list_images_with_filter(client):
    """Test listing images filtered by user_id"""
    user_id = '12345'
    response = client.get(f'/images?user_id={user_id}')
    assert response.status_code == 200
    images = response.get_json()
    for image in images:
        assert image['metadata']['user_id'] == user_id  # Ensure the filtered images match the user_id


### Test Cases for the View/Download Image API

def test_view_image_success(client):
    """Test successfully viewing/downloading an image"""
    # First, upload an image to get an image_id
    data = {
        'user_id': '12345',
        'title': 'View Image Test',
        'description': 'Test image for view API'
    }
    upload_response = client.post('/upload', data={
        'image': (BytesIO(b'fake image data'), 'view_image_test.jpg'),
        'user_id': data['user_id'],
        'title': data['title'],
        'description': data['description']
    })
    image_id = upload_response.get_json()['image_id']

    # Now, try viewing the image by its ID
    response = client.get(f'/image/{image_id}')
    assert response.status_code == 200
    assert 'image_url' in response.get_json()


def test_view_image_not_found(client):
    """Test viewing an image that does not exist"""
    response = client.get('/image/non_existing_id')
    assert response.status_code == 404  # Expecting a 404 Not Found
    assert response.get_json()['error'] == 'Image not found'


### Test Cases for the Delete Image API

def test_delete_image_success(client):
    """Test successfully deleting an image"""
    # First, upload an image to get an image_id
    data = {
        'user_id': '12345',
        'title': 'Delete Image Test',
        'description': 'Test image for delete API'
    }
    upload_response = client.post('/upload', data={
        'image': (BytesIO(b'fake image data'), 'delete_image_test.jpg'),
        'user_id': data['user_id'],
        'title': data['title'],
        'description': data['description']
    })
    image_id = upload_response.get_json()['image_id']

    # Now, try deleting the image
    response = client.delete(f'/image/{image_id}')
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Image deleted successfully'


def test_delete_image_not_found(client):
    """Test deleting an image that does not exist"""
    response = client.delete('/image/non_existing_id')
    assert response.status_code == 404  # Expecting a 404 Not Found
    assert response.get_json()['error'] == 'Image not found'