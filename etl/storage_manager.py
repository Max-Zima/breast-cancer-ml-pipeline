"""
Модуль интеграции с облачными хранилищами.

Этот модуль предоставляет единый интерфейс для работы с различными типами
хранилищ данных: локальная файловая система, Dropbox, Google Cloud Storage
и Amazon S3.
"""

import json
import logging
import os
import sys
from typing import Any, Dict

# Добавление родительской директории в путь для импортов
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LocalStorage:
    """Реализация хранилища в локальной файловой системе."""

    def __init__(self, base_path: str = "results"):
        """Инициализация локального хранилища.
        
        Args:
            base_path: Базовый путь для хранения файлов.
        """
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        logger.info(f"Инициализировано локальное хранилище в {base_path}")

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Загрузка файла в локальное хранилище (проверка существования файла).
        
        Args:
            local_path: Путь к локальному файлу.
            remote_path: Удаленный путь (не используется для локального хранилища).
            
        Returns:
            True если файл существует, False в противном случае.
        """
        try:
            # Для локального хранилища просто проверяем, что файл существует
            if os.path.exists(local_path):
                logger.info(f"Файл подтвержден в локальном хранилище: {local_path}")
                return True
            else:
                logger.error(f"Файл не найден: {local_path}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при проверке файла: {str(e)}")
            return False

    def list_files(self) -> list:
        """Получение списка файлов в хранилище.
        
        Returns:
            Список относительных путей к файлам.
        """
        try:
            files = []
            for root, dirs, filenames in os.walk(self.base_path):
                for filename in filenames:
                    rel_path = os.path.relpath(
                        os.path.join(root, filename), self.base_path                    )
                    files.append(rel_path)
            return files
        except Exception as e:
            logger.error(f"Ошибка при получении списка файлов: {str(e)}")
            return []


class DropboxStorage:
    """Реализация хранилища Dropbox."""

    def __init__(self, access_token: str):
        """Инициализация хранилища Dropbox.
        
        Args:
            access_token: Токен доступа для Dropbox API.
        """
        self.access_token = access_token
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Инициализация клиента Dropbox."""
        try:
            import dropbox
            
            self.client = dropbox.Dropbox(self.access_token)
            # Тестирование соединения
            self.client.users_get_current_account()
            logger.info("Клиент Dropbox инициализирован успешно")
        except ImportError:
            logger.error("Библиотека Dropbox не установлена")
            raise ImportError("Установите библиотеку dropbox: pip install dropbox")
        except Exception as e:
            logger.error(f"Ошибка инициализации клиента Dropbox: {str(e)}")
            raise

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Загрузка файла в Dropbox.
        
        Args:
            local_path: Путь к локальному файлу.
            remote_path: Удаленный путь в Dropbox.
            
        Returns:
            True если загрузка успешна, False в противном случае.
        """
        try:
            if not self.client:
                raise ValueError("Клиент Dropbox не инициализирован")

            with open(local_path, "rb") as f:
                self.client.files_upload(
                    f.read(),
                    f"/{remote_path}",
                    mode=dropbox.files.WriteMode("overwrite"),
                )
            logger.info(f"Файл загружен в Dropbox: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка загрузки в Dropbox: {str(e)}")
            return False

    def list_files(self, folder: str = "") -> list:
        """Получение списка файлов в папке Dropbox.
        
        Args:
            folder: Имя папки для поиска файлов.
            
        Returns:
            Список имен файлов.
        """
        try:
            if not self.client:
                raise ValueError("Клиент Dropbox не инициализирован")

            result = self.client.files_list_folder(f"/{folder}")
            files = [entry.name for entry in result.entries]
            return files
        except Exception as e:
            logger.error(f"Ошибка получения списка файлов Dropbox: {str(e)}")
            return []


class GCSStorage:
    """Реализация хранилища Google Cloud Storage."""

    def __init__(self, bucket_name: str, credentials_path: str = None):
        """Инициализация хранилища GCS.
        
        Args:
            bucket_name: Имя корзины GCS.
            credentials_path: Путь к файлу учетных данных (опционально).
        """
        self.bucket_name = bucket_name
        self.credentials_path = credentials_path
        self.client = None
        self.bucket = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize GCS client"""
        try:
            from google.cloud import storage

            if self.credentials_path:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.credentials_path

            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
            logger.info(f"GCS client initialized for bucket: {self.bucket_name}")
        except ImportError:
            logger.error("Библиотека Google Cloud Storage не установлена")
            raise ImportError("Установите: pip install google-cloud-storage")
        except Exception as e:
            logger.error(f"Error initializing GCS client: {str(e)}")
            raise

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to GCS"""
        try:
            if not self.bucket:
                raise ValueError("GCS bucket not initialized")

            blob = self.bucket.blob(remote_path)
            blob.upload_from_filename(local_path)
            logger.info(f"File uploaded to GCS: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"Error uploading to GCS: {str(e)}")
            return False

    def list_files(self, prefix: str = "") -> list:
        """List files in GCS bucket"""
        try:
            if not self.bucket:
                raise ValueError("GCS bucket not initialized")

            blobs = self.bucket.list_blobs(prefix=prefix)
            files = [blob.name for blob in blobs]
            return files
        except Exception as e:
            logger.error(f"Error listing GCS files: {str(e)}")
            return []


class S3Storage:
    """Amazon S3 storage implementation"""

    def __init__(
        self, bucket_name: str, access_key: str = None, secret_key: str = None
    ):
        self.bucket_name = bucket_name
        self.access_key = access_key
        self.secret_key = secret_key
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize S3 client"""
        try:
            import boto3

            if self.access_key and self.secret_key:
                self.client = boto3.client(
                    "s3",
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                )
            else:
                # Use default credentials
                self.client = boto3.client("s3")

            # Test connection
            self.client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
        except ImportError:
            logger.error("Boto3 library not installed")
            raise ImportError("Install boto3 library: pip install boto3")
        except Exception as e:
            logger.error(f"Error initializing S3 client: {str(e)}")
            raise

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to S3"""
        try:
            if not self.client:
                raise ValueError("S3 client not initialized")

            self.client.upload_file(local_path, self.bucket_name, remote_path)
            logger.info(f"File uploaded to S3: {remote_path}")
            return True
        except Exception as e:
            logger.error(f"Error uploading to S3: {str(e)}")
            return False

    def list_files(self, prefix: str = "") -> list:
        """List files in S3 bucket"""
        try:
            if not self.client:
                raise ValueError("S3 client not initialized")

            response = self.client.list_objects_v2(
                Bucket=self.bucket_name, Prefix=prefix
            )
            files = [obj["Key"] for obj in response.get("Contents", [])]
            return files
        except Exception as e:
            logger.error(f"Error listing S3 files: {str(e)}")
            return []


def get_storage_client(storage_type: str, **kwargs) -> Any:
    """
    Factory function to create storage client

    Args:
        storage_type: Type of storage (local, dropbox, gcs, s3)
        **kwargs: Storage-specific configuration

    Returns:
        Storage client instance
    """
    storage_type = storage_type.lower()

    if storage_type == "local":
        return LocalStorage(kwargs.get("base_path", "results"))
    elif storage_type == "dropbox":
        return DropboxStorage(kwargs.get("access_token"))
    elif storage_type == "gcs":
        return GCSStorage(kwargs.get("bucket_name"), kwargs.get("credentials_path"))
    elif storage_type == "s3":
        return S3Storage(
            kwargs.get("bucket_name"),
            kwargs.get("access_key"),
            kwargs.get("secret_key"),
        )
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")


def upload_results(
    storage_config: Dict[str, Any], results_dir: str = "results"
) -> bool:
    """
    Upload all results to configured storage

    Args:
        storage_config: Storage configuration
        results_dir: Directory containing results

    Returns:
        True if successful
    """
    try:
        logger.info("Starting results upload")

        # Get storage client
        storage_type = storage_config.get("type", "local")
        client = get_storage_client(storage_type, **storage_config)

        # Find all result files
        result_files = []
        for root, dirs, files in os.walk(results_dir):
            for file in files:
                local_path = os.path.join(root, file)
                remote_path = os.path.relpath(local_path, results_dir)
                result_files.append((local_path, remote_path))

        # Upload each file
        success_count = 0
        for local_path, remote_path in result_files:
            if client.upload_file(local_path, remote_path):
                success_count += 1

        logger.info(f"Uploaded {success_count}/{len(result_files)} files")

        # Create upload summary
        upload_summary = {
            "storage_type": storage_type,
            "total_files": len(result_files),
            "successful_uploads": success_count,
            "files": [remote_path for _, remote_path in result_files],
        }

        # Save upload summary
        with open(os.path.join(results_dir, "upload_summary.json"), "w") as f:
            json.dump(upload_summary, f, indent=2)

        return success_count == len(result_files)

    except Exception as e:
        logger.error(f"Error uploading results: {str(e)}")
        return False


def main():
    """Main function for standalone execution"""
    try:
        # Configuration for local storage (default)
        storage_config = {"type": "local", "base_path": "results"}

        # Check for environment variables
        storage_type = os.getenv("STORAGE_TYPE", "local")

        if storage_type == "dropbox":
            storage_config = {
                "type": "dropbox",
                "access_token": os.getenv("DROPBOX_ACCESS_TOKEN"),
            }
        elif storage_type == "gcs":
            storage_config = {
                "type": "gcs",
                "bucket_name": os.getenv("GCS_BUCKET_NAME"),
                "credentials_path": os.getenv("GCS_CREDENTIALS_PATH"),
            }
        elif storage_type == "s3":
            storage_config = {
                "type": "s3",
                "bucket_name": os.getenv("S3_BUCKET_NAME"),
                "access_key": os.getenv("AWS_ACCESS_KEY_ID"),
                "secret_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
            }

        # Upload results
        success = upload_results(storage_config)

        if success:
            logger.info("All results uploaded successfully")
            print("Results upload completed successfully")
        else:
            logger.warning("Some files failed to upload")
            print("Results upload completed with warnings")

    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise


if __name__ == "__main__":
    main()
