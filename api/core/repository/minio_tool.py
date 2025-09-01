from minio import Minio
import config 

class MinioTool:
    def __init__(self, bucket_name: str = "capivara"):
        self.bucket_name = bucket_name
        self.minio_client = Minio(
            f"{config.MINIO_HOST}:{config.MINIO_PORT}",
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
        )

    def upload_file(self, file_path: str, file_name: str, content_type: str = "application/octet-stream"):
        self.minio_client.fput_object(self.bucket_name, file_name, file_path, content_type=content_type)

    def download_file(self, file_name: str, file_path: str, content_type: str = "application/octet-stream"):
        self.minio_client.fget_object(self.bucket_name, file_name, file_path, content_type=content_type)

    def delete_file(self, file_name: str):
        self.minio_client.remove_object(self.bucket_name, file_name)

    def list_files(self, prefix: str = ""):
        return self.minio_client.list_objects(self.bucket_name, prefix=prefix)
    
    def get_file_url(self, file_name: str):
        return self.minio_client.presigned_get_object(self.bucket_name, file_name)