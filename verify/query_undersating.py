if __name__ == "__main__":
    print("=== Query Understanding Test ===")

    question = "How do I configure webhook retry backoff in Notion-Version 2021-05-13?"


    print(f"\nQuestion:\n{question}\n")

    result = understand_query(question)

    print("=== Gemini Output ===")
    print(json.dumps(result, indent=2))

    print("\n=== Validation ===")

    if not isinstance(result, dict):
        raise RuntimeError("FAIL: Gemini did not return a JSON object.")

    print("PASS: Response is a JSON object.")

    required_fields = [
        "intent",
        "version",
    ]

    for field in required_fields:
        if field in result:
            print(f"PASS: '{field}' = {result[field]}")
        else:
            print(f"WARNING: '{field}' is missing.")

    if result.get("version") in KNOWN_VERSIONS:
        print("PASS: Version is a known version.")
    elif result.get("version") in (None, ""):
        print("PASS: No version specified.")
    else:
        print(f"WARNING: Unknown version returned: {result.get('version')}")