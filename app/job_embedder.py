
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types


BASE_DIR = Path(__file__).resolve().parent.parent

CHUNKS_PATH = BASE_DIR / "data" / "job_chunks.json"
EMBEDDINGS_PATH = BASE_DIR / "data" / "job_embeddings.npy"
CHECKPOINT_PATH = BASE_DIR / "data" / "embedding_checkpoint.npz"
METADATA_PATH = BASE_DIR / "data" / "job_index_metadata.json"

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768

BATCH_SIZE = 20
MAX_RETRIES = 5
BATCH_DELAY = 15


def create_client():
    load_dotenv()

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing from .env")

    return genai.Client(api_key=api_key)


def load_chunks():
    with open(CHUNKS_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def get_dataset_signature(chunks):
    payload = json.dumps(
        {
            "model": EMBEDDING_MODEL,
            "dimensions": EMBEDDING_DIMENSIONS,
            "task_type": "RETRIEVAL_DOCUMENT",
            "chunks": chunks
        },
        sort_keys=True,
        ensure_ascii=False
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


def normalize_vectors(vectors):
    vectors = np.asarray(vectors, dtype=np.float32)

    if not np.all(np.isfinite(vectors)):
        raise ValueError("Invalid numerical values in embeddings.")

    norms = np.linalg.norm(
        vectors, axis=1, keepdims=True
    )

    if np.any(norms == 0):
        raise ValueError("Zero-length embedding detected.")

    return vectors / norms


def embed_batch(client, texts):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=EMBEDDING_DIMENSIONS
                )
            )

            vectors = np.asarray(
                [item.values for item in response.embeddings],
                dtype=np.float32
            )

            expected_shape = (
                len(texts),
                EMBEDDING_DIMENSIONS
            )

            if vectors.shape != expected_shape:
                raise ValueError(
                    f"Unexpected embedding shape: {vectors.shape}"
                )

            return normalize_vectors(vectors)

        except Exception as error:
            status = getattr(error, "code", None)

            if status not in (429, 500, 502, 503, 504):
                raise

            print(
                f"Attempt {attempt}/{MAX_RETRIES} failed: "
                f"{error}"
            )

            if attempt == MAX_RETRIES:
                raise

            wait_time = (
    65 if status == 429
    else min(60, 5 * (2 ** (attempt - 1)))
)

            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)


def save_checkpoint(vectors, signature):
    temp_path = CHECKPOINT_PATH.with_suffix(".tmp.npz")

    np.savez_compressed(
        temp_path,
        embeddings=vectors,
        signature=signature
    )

    os.replace(temp_path, CHECKPOINT_PATH)


def load_checkpoint(signature, total_chunks):
    if not CHECKPOINT_PATH.exists():
        return np.empty(
            (0, EMBEDDING_DIMENSIONS),
            dtype=np.float32
        )

    with np.load(
        CHECKPOINT_PATH, allow_pickle=False
    ) as checkpoint:

        saved_signature = str(
            checkpoint["signature"].item()
        )

        if saved_signature != signature:
            raise ValueError(
                "Dataset or embedding configuration changed. "
                "Existing checkpoint cannot be reused."
            )

        vectors = checkpoint["embeddings"]

    if (
        vectors.ndim != 2
        or vectors.shape[1] != EMBEDDING_DIMENSIONS
        or len(vectors) > total_chunks
        or not np.all(np.isfinite(vectors))
    ):
        raise ValueError("Invalid embedding checkpoint.")

    print(
        f"Resuming from {len(vectors)} saved embeddings."
    )

    return vectors


def generate_embeddings():
    chunks = load_chunks()

    if not chunks:
        raise ValueError("No chunks found.")

    signature = get_dataset_signature(chunks)

    all_vectors = load_checkpoint(
        signature, len(chunks)
    )

    completed = len(all_vectors)
    total = len(chunks)

    print("\n--- Embedding Generation ---")
    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Dimensions: {EMBEDDING_DIMENSIONS}")
    print(f"Total chunks: {total}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Already completed: {completed}")

    client = create_client() if completed < total else None

    for start in range(completed, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)

        batch = chunks[start:end]

        texts = [
            chunk["text"] for chunk in batch
        ]

        batch_vectors = embed_batch(client, texts)

        all_vectors = np.concatenate(
            [all_vectors, batch_vectors],
            axis=0
        )

        save_checkpoint(all_vectors, signature)

        percentage = len(all_vectors) / total * 100

        print(
            f"Progress: {len(all_vectors)}/{total} "
            f"({percentage:.2f}%)"
        )

        if end < total:
            time.sleep(BATCH_DELAY)

    np.save(EMBEDDINGS_PATH, all_vectors)

    metadata = {
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimensions": EMBEDDING_DIMENSIONS,
        "task_type": "RETRIEVAL_DOCUMENT",
        "similarity_metric": "cosine",
        "normalized": True,
        "total_chunks": total,
        "dataset_signature": signature,
        "chunk_ids": [
            chunk["chunk_id"] for chunk in chunks
        ]
    }

    with open(
        METADATA_PATH, "w", encoding="utf-8"
    ) as file:
        json.dump(
            metadata,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\n--- Embedding Generation Completed ---")
    print(f"Total embeddings: {len(all_vectors)}")
    print(f"Embedding shape: {all_vectors.shape}")
    print(f"Embeddings saved to: {EMBEDDINGS_PATH}")
    print(f"Metadata saved to: {METADATA_PATH}")

    return all_vectors


if __name__ == "__main__":
    generate_embeddings()
