import os
import google.auth
import googleapiclient.discovery
import googleapiclient.errors

def upload_video_to_youtube(video_file_path, title, description, privacy_status):
    # Set your Service Account credentials file path
    credentials_file = './lifechurchapp-322612-5c538209723d.json'

    # Create the credentials object
    credentials, project = google.auth.load_credentials_from_file(credentials_file)

    # Create the YouTube Data API client
    youtube = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)

    # Create the video resource
    request_body = {
        'snippet': {
            'title': title,
            'description': description
        },
        'status': {
            'privacyStatus': privacy_status
        }
    }

    try:
        # Execute the API request to upload the video
        response = youtube.videos().insert(
            part='snippet,status',
            body=request_body,
            media_body=video_file_path
        ).execute()

        video_id = response['id']
        print(f"Video uploaded successfully! Video ID: {video_id}")
    except googleapiclient.errors.HttpError as e:
        print(f"An error occurred: {e}")
        return

# Set the path to your video file
video_path = './videos/test_video.mp4'
# Set the video metadata
video_title = 'My Uploaded Video'
video_description = 'This is a test video upload'
privacy_status = 'private'  # Other options: 'public', 'unlisted'

# Call the upload function
upload_video_to_youtube(video_path, video_title, video_description, privacy_status)
