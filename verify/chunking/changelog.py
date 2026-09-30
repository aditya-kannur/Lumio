if __name__ == "__main__":
    from pathlib import Path

    changelog_path = Path("data/changelog/changelog.md")

    if not changelog_path.exists():
        raise FileNotFoundError(
            f"Changelog file not found: {changelog_path}"
        )

    text = changelog_path.read_text(
        encoding="utf-8"
    )

    chunks = chunk_changelog(text)

    print("\n=== CHANGELOG CHUNKER TEST ===")
    print(f"File: {changelog_path}")
    print(f"Total chunks: {len(chunks)}")

    if not chunks:
        raise RuntimeError(
            "FAIL: No chunks were created."
        )

    print("PASS: Chunks created.")

    # --------------------------------------------------------------
    # Validate every chunk
    # --------------------------------------------------------------

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        required_fields = {
            "text",
            "doc_type",
            "release_date",
            "chunk_id",
        }

        missing = required_fields - chunk.keys()

        if missing:
            raise RuntimeError(
                f"FAIL: Chunk {index} missing fields: {missing}"
            )

        if not chunk["chunk_id"]:
            raise RuntimeError(
                f"FAIL: Chunk {index} has empty chunk_id."
            )

    print(
        "PASS: Every chunk contains "
        "text, doc_type, release_date, and chunk_id."
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

    print("PASS: All chunk_ids are unique.")

    # --------------------------------------------------------------
    # Show first 10 chunks
    # --------------------------------------------------------------

    print("\n=== SAMPLE CHUNKS ===")

    for index, chunk in enumerate(
        chunks[:10],
        start=1,
    ):
        print(f"\n--- Chunk {index} ---")
        print(f"chunk_id:     {chunk['chunk_id']}")
        print(f"release_date: {chunk['release_date']}")
        print(f"doc_type:     {chunk['doc_type']}")
        print(f"text length:  {len(chunk['text'])}")
        print("text:")
        print(chunk["text"])

    # --------------------------------------------------------------
    # Verify deterministic IDs
    # --------------------------------------------------------------

    chunks_again = chunk_changelog(text)

    ids_again = [
        chunk["chunk_id"]
        for chunk in chunks_again
    ]

    if chunk_ids != ids_again:
        raise RuntimeError(
            "FAIL: chunk_ids changed when the same "
            "input was processed again."
        )

    print(
        "\nPASS: chunk_ids are deterministic."
    )

    print(
        "\nALL CHANGELOG CHUNKER TESTS PASSED."
    )