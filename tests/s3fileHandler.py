import boto3
import botocore
import os 

# upload all files ending with extn in current directory to s3 bucket
def upload_files_s3 (bucket, extn='json'):

    session = boto3.Session()
    client = session.client('s3')

    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for f in files:
        if f.endswith(extn):
            print ("uploading to s3: ", f)
            client.upload_file(f'{f}', bucket, f'outputs/{f}')

# look for filename locally or in s3 bucket
def get_data_s3 (bucket, filename):

    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for f in files:
        if (f == filename):
            print ("The data file was found locally...")
            return filename

    # look in s3 bucket    
    session = boto3.Session()
    client = session.client('s3')
    try:
        client.download_file(bucket, filename, filename) # writes file to the same location on local
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print(f"The data file does not exist: {filename}")
            return "file-not-found"
        else:
            raise Exception("Other errors encountered when searching for data file in s3.") 

    return filename

