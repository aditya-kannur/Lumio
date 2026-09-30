if __name__ == "__main__":
    from pathlib import Path

    reference_path = Path(
        "data/reference/openapi.json"
    )

    if not reference_path.exists():
        raise FileNotFoundError(
            f"Reference file not found: "
            f"{reference_path}"
        )

    chunks = chunk_reference_file(
        str(reference_path)
    )

    print("\n=== REFERENCE CHUNKER TEST ===")
    print(f"File: {reference_path}")
    print(f"Total chunks: {len(chunks)}")

    if not chunks:
        raise RuntimeError(
            "FAIL: No reference chunks created."
        )

    print("PASS: Chunks created.")

    # --------------------------------------------------------------
    # Validate every chunk
    # --------------------------------------------------------------

    required_fields = {
        "doc_type",
        "endpoint",
        "method",
        "tags",
        "summary",
        "version",
        "text",
        "chunk_id",
    }

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        missing = (
            required_fields - chunk.keys()
        )

        if missing:
            raise RuntimeError(
                f"FAIL: Chunk {index} "
                f"missing fields: {missing}"
            )

        if not chunk["chunk_id"]:
            raise RuntimeError(
                f"FAIL: Chunk {index} "
                "has empty chunk_id."
            )

    print(
        "PASS: Every chunk contains "
        "all required fields."
    )

    # --------------------------------------------------------------
    # Validate chunk IDs are unique
    # --------------------------------------------------------------

    chunk_ids = [
        chunk["chunk_id"]
        for chunk in chunks
    ]

    if len(chunk_ids) != len(set(chunk_ids)):
        raise RuntimeError(
            "FAIL: Duplicate chunk_ids detected."
        )

    print(
        "PASS: All chunk_ids are unique."
    )

    # --------------------------------------------------------------
    # Validate endpoint/method identity
    # --------------------------------------------------------------

    identities = [
        (
            chunk["version"],
            chunk["method"],
            chunk["endpoint"],
        )
        for chunk in chunks
    ]

    if len(identities) != len(set(identities)):
        raise RuntimeError(
            "FAIL: Duplicate "
            "version/method/endpoint combinations detected."
        )

    print(
        "PASS: Endpoint identities are unique."
    )

    # --------------------------------------------------------------
    # Show first 10 chunks
    # --------------------------------------------------------------

    print("\n=== SAMPLE CHUNKS ===")

    for index, chunk in enumerate(
        chunks[:10],
        start=1,
    ):
        print(f"\n--- Chunk {index} ---")
        print(
            f"chunk_id: {chunk['chunk_id']}"
        )
        print(
            f"endpoint: {chunk['endpoint']}"
        )
        print(
            f"method:   {chunk['method']}"
        )
        print(
            f"version:  {chunk['version']}"
        )
        print(
            f"summary:  {chunk['summary']}"
        )
        print(
            f"text:     {chunk['text']}"
        )

    # --------------------------------------------------------------
    # Deterministic ID test
    # --------------------------------------------------------------

    chunks_again = chunk_reference_file(
        str(reference_path)
    )

    ids_again = [
        chunk["chunk_id"]
        for chunk in chunks_again
    ]

    if chunk_ids != ids_again:
        raise RuntimeError(
            "FAIL: chunk_ids changed when the "
            "same reference file was processed twice."
        )

    print(
        "\nPASS: chunk_ids are deterministic."
    )

    print(
        "\nALL REFERENCE CHUNKER TESTS PASSED."
    )