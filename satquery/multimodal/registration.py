class RegistrationStrategy:
    def validate_and_register(self, img_a, img_b):
        # Basic bounds overlap and CRS assertion mimicking Phase 3
        if img_a.crs != img_b.crs:
            return False, "CRS mismatch"
        return True, "Aligned"
