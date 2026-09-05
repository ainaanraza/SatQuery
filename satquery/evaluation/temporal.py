def evaluate_temporal(dataset):
    successful_pairs = 0
    failed_pairs = 0

    for pair in dataset:
        if pair.get("success") is True:
            successful_pairs += 1
        else:
            failed_pairs += 1

    return {
        "successful_pairs": successful_pairs,
        "failed_pairs": failed_pairs
    }