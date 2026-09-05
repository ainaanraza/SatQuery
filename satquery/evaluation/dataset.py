import json


class DatasetManifest:
    def __init__(self, path):
        self.path = path

    def load(self):
        with open(self.path, "r", encoding="utf-8") as file:
            return json.load(file)

    def check_leakage(self, splits):
        seen_images = {}
        leakage = []

        for split_name, records in splits.items():
            for record in records:
                for key in ("image_a", "image_b"):
                    image = record.get(key)

                    if image is None:
                        continue

                    if image in seen_images:
                        leakage.append({
                            "image": image,
                            "first_split": seen_images[image],
                            "second_split": split_name
                        })
                    else:
                        seen_images[image] = split_name

        return {
            "leakage_detected": len(leakage) > 0,
            "leakage": leakage
        }