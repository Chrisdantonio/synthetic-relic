from google.cloud import storage


def download_public_file(bucket_name, source_blob_name, destination_file_name):
    """Downloads a public blob from the bucket."""
    bucket_name = "quickdraw_dataset"
    source_blob_name = "full/simplified/"
    destination_file_name = "/Users/christopherdantonio/Desktop/synthetic-relic/googdrawings"

    storage_client = storage.Client.create_anonymous_client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

    print(
        "Downloaded public blob {} from bucket {} to {}.".format(
            source_blob_name, bucket.name, destination_file_name
        )
    )
