if __name__ == "__main__":
    import os

    data_dir = "data/migrations"

    files = sorted(
        filename
        for filename in os.listdir(data_dir)
        if filename.endswith(".md")
    )

    if not files:
        raise RuntimeError(
            "FAIL: No migration files found."
        )

    all_chunks = []

    for filename in files:
        filepath = os.path.join(
            data_dir,
            filename,
        )

        chunks = chunk_migration_file(
            filepath
        )

        print(f"\n=== {filename} ===")
        print(
            f"Version: "
            f"{extract_version_from_filename(filename)}"
        )
        print(f"Chunks: {len(chunks)}")

        if not chunks:
            raise RuntimeError(
                f"FAIL: No chunks created from {filename}"
            )

        # Validate fields
        for index, chunk in enumerate(
            chunks,
            start=1,
        ):
            required_fields = {
                "doc_type",
                "version",
                "section",
                "breaking",
                "text",
                "chunk_id",
            }

            missing = (
                required_fields - chunk.keys()
            )

            if missing:
                raise RuntimeError(
                    f"FAIL: {filename} chunk {index} "
                    f"missing fields: {missing}"
                )

            if not chunk["chunk_id"]:
                raise RuntimeError(
                    f"FAIL: {filename} chunk {index} "
                    "has empty chunk_id."
                )

        # Validate IDs are unique within this file
        ids = [
            chunk["chunk_id"]
            for chunk in chunks
        ]

        if len(ids) != len(set(ids)):
            raise RuntimeError(
                f"FAIL: Duplicate chunk_ids "
                f"found in {filename}"
            )

        print(
            "PASS: Fields and chunk_ids valid."
        )

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):
            print(f"\n--- Chunk {index} ---")
            print(f"chunk_id: {chunk['chunk_id']}")
            print(f"section:  {chunk['section']}")
            print(f"version:  {chunk['version']}")
            print(f"breaking: {chunk['breaking']}")
            print(
                f"text length: {len(chunk['text'])}"
            )
            print(
                f"text: {chunk['text'][:300]}"
            )

        all_chunks.extend(chunks)

    # --------------------------------------------------------------
    # Validate global ID uniqueness
    # --------------------------------------------------------------

    all_ids = [
        chunk["chunk_id"]
        for chunk in all_chunks
    ]

    if len(all_ids) != len(set(all_ids)):
        raise RuntimeError(
            "FAIL: Duplicate chunk_ids detected "
            "across migration files."
        )

    print("\n==============================")
    print(f"Migration files: {len(files)}")
    print(f"Total chunks:   {len(all_chunks)}")
    print("==============================")

    print(
        "PASS: All migration chunk_ids are unique."
    )

    # --------------------------------------------------------------
    # Deterministic ID test
    # --------------------------------------------------------------

    first_file = os.path.join(
        data_dir,
        files[0],
    )

    first_run = chunk_migration_file(
        first_file
    )

    second_run = chunk_migration_file(
        first_file
    )

    first_ids = [
        chunk["chunk_id"]
        for chunk in first_run
    ]

    second_ids = [
        chunk["chunk_id"]
        for chunk in second_run
    ]

    if first_ids != second_ids:
        raise RuntimeError(
            "FAIL: chunk_ids changed when the "
            "same migration file was processed twice."
        )

    print(
        "PASS: chunk_ids are deterministic."
    )

    print(
        "\nALL MIGRATION CHUNKER TESTS PASSED."
    )