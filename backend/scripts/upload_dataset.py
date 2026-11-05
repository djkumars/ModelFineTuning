import os
from pathlib import Path

from azure.storage.blob import BlobServiceClient


def main() -> None:
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if not connection_string:
        raise SystemExit("AZURE_STORAGE_CONNECTION_STRING must be set.")

    container_name = os.getenv("AZURE_STORAGE_CONTAINER", "ticket-training-data")
    data_directory = Path(__file__).resolve().parents[2] / "data"
    service = BlobServiceClient.from_connection_string(connection_string)
    container = service.get_container_client(container_name)
    if not container.exists():
        container.create_container()

    for filename in ("train.jsonl", "validation.jsonl"):
        path = data_directory / filename
        if not path.is_file():
            raise FileNotFoundError(f"Dataset file not found: {path}")
        with path.open("rb") as dataset:
            container.upload_blob(filename, dataset, overwrite=True)
        print(f"Uploaded {filename} to container {container_name}.")


if __name__ == "__main__":
    main()
