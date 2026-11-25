
import json
import time

import numpy as np
from google.genai import types

from app.job_embedder import (
    BASE_DIR,
    CHUNKS_PATH,
    EMBEDDINGS_PATH,
    METADATA_PATH,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
    MAX_RETRIES,
    create_client,
    get_dataset_signature,
    normalize_vectors
)


DATASET_PATH = BASE_DIR / "data" / "internships.json"


class JobRetriever:

    def __init__(self):
        self.chunks = self.load_json(CHUNKS_PATH)
        self.metadata = self.load_json(METADATA_PATH)

        self.embeddings = np.load(
            EMBEDDINGS_PATH,
            allow_pickle=False
        )

        jobs = self.load_json(DATASET_PATH)

        self.jobs = {
            job["job_id"]: job for job in jobs
        }

        self.validate_index()

        self.client = create_client()

    @staticmethod
    def load_json(path):
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def validate_index(self):
        expected_shape = (
            len(self.chunks),
            EMBEDDING_DIMENSIONS
        )

        if not self.chunks:
            raise ValueError("Vector index is empty.")

        if self.embeddings.shape != expected_shape:
            raise ValueError("Embedding shape mismatch.")

        if not np.all(np.isfinite(self.embeddings)):
            raise ValueError("Invalid embedding values.")

        norms = np.linalg.norm(
            self.embeddings, axis=1
        )

        if not np.allclose(norms, 1.0, atol=1e-5):
            raise ValueError("Embeddings are not normalized.")

        if self.metadata["embedding_model"] != EMBEDDING_MODEL:
            raise ValueError("Embedding model mismatch.")

        if (
            self.metadata["embedding_dimensions"]
            != EMBEDDING_DIMENSIONS
        ):
            raise ValueError("Embedding dimensions mismatch.")

        if self.metadata["total_chunks"] != len(self.chunks):
            raise ValueError("Metadata chunk count mismatch.")

        chunk_ids = [
            chunk["chunk_id"]
            for chunk in self.chunks
        ]

        if self.metadata["chunk_ids"] != chunk_ids:
            raise ValueError("Chunk ID mapping mismatch.")

        if (
            self.metadata["dataset_signature"]
            != get_dataset_signature(self.chunks)
        ):
            raise ValueError("Dataset signature mismatch.")

        if any(
            chunk["job_id"] not in self.jobs
            for chunk in self.chunks
        ):
            raise ValueError("Unknown job ID in vector index.")

    def embed_query(self, query):
        query = query.strip()

        if not query:
            raise ValueError("Search query cannot be empty.")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=query,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_QUERY",
                        output_dimensionality=EMBEDDING_DIMENSIONS
                    )
                )

                vector = np.asarray(
                    response.embeddings[0].values,
                    dtype=np.float32
                )

                if vector.shape != (EMBEDDING_DIMENSIONS,):
                    raise ValueError(
                        "Unexpected query embedding shape."
                    )

                return normalize_vectors(
                    vector.reshape(1, -1)
                )[0]

            except Exception as error:
                status = getattr(error, "code", None)

                if (
                    status not in (429, 500, 502, 503, 504)
                    or attempt == MAX_RETRIES
                ):
                    raise

                wait_time = (
                    65 if status == 429
                    else min(60, 5 * (2 ** (attempt - 1)))
                )

                print(
                    f"Query embedding failed. "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

    def search(self, query, top_k=5):

        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")

        query_vector = self.embed_query(query)

        # Cosine similarity using normalized vectors
        scores = self.embeddings @ query_vector

        scores = np.clip(scores, -1.0, 1.0)

        ranked_indices = np.argsort(-scores)

        job_results = {}

        for index in ranked_indices:
            chunk = self.chunks[index]
            job_id = chunk["job_id"]
            score = float(scores[index])

            if job_id not in job_results:
                job = self.jobs[job_id]

                job_results[job_id] = {
                    "job_id": job_id,
                    "job_title": job["job_title"],
                    "company": job["company"],
                    "location": job["location"],
                    "domain": job["domain"],
                    "work_mode": job["work_mode"],
                    "semantic_score": score,
                    "best_matching_section": chunk["section"],
                    "matched_chunks": [],
                    "job": job
                }

            result = job_results[job_id]

            if len(result["matched_chunks"]) < 3:
                result["matched_chunks"].append({
                    "chunk_id": chunk["chunk_id"],
                    "section": chunk["section"],
                    "similarity_score": score,
                    "text": chunk["text"]
                })

        ranked_jobs = sorted(
            job_results.values(),
            key=lambda item: item["semantic_score"],
            reverse=True
        )

        return ranked_jobs[:top_k]


def main():
    retriever = JobRetriever()

    print("\n--- Internship Semantic Search ---")
    print(f"Indexed chunks: {len(retriever.chunks)}")
    print(f"Available jobs: {len(retriever.jobs)}")
    print(f"Embedding model: {EMBEDDING_MODEL}")

    while True:
        query = input(
            "\nEnter search query (or 'exit'): "
        ).strip()

        if query.lower() == "exit":
            print("Search session ended.")
            break

        if not query:
            print("Please enter a valid query.")
            continue

        try:
            results = retriever.search(query, top_k=5)

            print("\n--- Top 5 Relevant Internships ---")

            for rank, result in enumerate(
                results, start=1
            ):
                print(f"\nRank {rank}")
                print(f"Job: {result['job_title']}")
                print(f"Company: {result['company']}")
                print(f"Location: {result['location']}")
                print(f"Domain: {result['domain']}")
                print(f"Work mode: {result['work_mode']}")

                print(
                    f"Semantic score: "
                    f"{result['semantic_score']:.4f}"
                )

                print(
                    f"Best matching section: "
                    f"{result['best_matching_section']}"
                )

                print("-" * 50)

        except Exception as error:
            print(f"Search failed: {error}")


if __name__ == "__main__":
    main()
