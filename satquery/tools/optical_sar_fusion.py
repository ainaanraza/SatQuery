import rasterio

from .base import SatQueryTool, ToolCapabilities, ToolResult
from .change_localization import localize_change
from satquery.evidence.models import Evidence
from satquery.multimodal.fusion import DEFAULT_NDWI_WATER, DEFAULT_SAR_WATER_DB, fuse_deterministic
from satquery.multimodal.optical import preprocess_optical
from satquery.multimodal.registration import DEFAULT_MAX_SIZE, common_grid
from satquery.multimodal.sar import preprocess_sar


MAX_SAR_BANDS = 2  # SAR products carry one or two polarisations


def assign_modalities(img_1, img_2):
    """Decide which input is optical and which is SAR; returns (optical, sar, warnings).

    Uses detected modality when available, otherwise assumes the given order (optical first).
    Raises ValueError when no input can plausibly be the SAR image.
    """
    modalities = (img_1.modality, img_2.modality)
    if modalities in (("sar", "sar"), ("optical", "optical")):
        raise ValueError(f"Both inputs were detected as {modalities[0]}; one optical and one SAR image are required.")

    if (img_1.modality == "sar" and img_2.modality != "sar") or (img_2.modality == "optical" and img_1.modality != "optical"):
        return img_2, img_1, [f"Treating {img_2.path} as optical and {img_1.path} as SAR based on detected modality."]

    warnings = []
    if img_2.modality != "sar":
        # Unknown modality: only accept a SAR-shaped raster, otherwise any image would be "fused".
        if img_2.band_count > MAX_SAR_BANDS:
            raise ValueError(
                f"Could not identify a SAR image: {img_2.path} has {img_2.band_count} bands and no SAR sensor tag "
                f"or polarisation band names (VV/VH/HH/HV)."
            )
        warnings.append(
            f"Modality not detected from metadata; assuming {img_1.path} is optical and {img_2.path} is SAR (input order)."
        )
    return img_1, img_2, warnings


class OpticalSARFusionTool(SatQueryTool):
    name = "optical_sar_fusion"
    description = "Fuses compatible optical and SAR data deterministically."
    capabilities = ToolCapabilities(cross_modal=True)

    def execute(self, context, arguments: dict) -> ToolResult:
        img_1 = arguments.get("optical_image")
        img_2 = arguments.get("sar_image")
        if img_1 is None or img_2 is None:
            return ToolResult(success=False, tool_name=self.name, errors=["An optical and a SAR image are required."])

        try:
            opt_img, sar_img, warnings = assign_modalities(img_1, img_2)
            # The SAR image is the reference grid; optical is resampled onto it.
            grid = common_grid(sar_img, opt_img, arguments.get("max_size", DEFAULT_MAX_SIZE))
            sar_rep = preprocess_sar(sar_img, grid["bounds"], grid["shape"])
            opt_rep = preprocess_optical(opt_img, grid["bounds"], grid["shape"])
            fusion = fuse_deterministic(
                opt_rep,
                sar_rep,
                sar_threshold_db=arguments.get("sar_threshold_db", DEFAULT_SAR_WATER_DB),
                ndwi_threshold=arguments.get("ndwi_threshold", DEFAULT_NDWI_WATER),
            )
        except (ValueError, rasterio.errors.RasterioError) as e:
            return ToolResult(success=False, tool_name=self.name, errors=[f"Optical-SAR fusion failed: {e}"])

        stats = fusion.data["statistics"]
        water = localize_change(fusion.data["sar_water_mask"], grid["transform"], grid["crs"])

        if stats["sar_calibration"] == "uncalibrated_dn":
            warnings.append("SAR values are uncalibrated digital numbers; the water threshold was chosen automatically (Otsu).")
        if stats["optical_water_index"] == "no_water_index":
            warnings.append("No green/NIR bands identified in the optical image descriptions; NDWI unavailable, water estimate is SAR-only.")
        if grid["downsample_factor"] > 1:
            warnings.append(f"Overlap was downsampled by {grid['downsample_factor']}x for fusion.")

        data = {
            "fusion_method": fusion.fusion_method,
            "optical_source": opt_img.path,
            "sar_source": sar_img.path,
            "statistics": stats,
            "sar_water_area_sqm": water["changed_area_sqm"],
            "sar_water_region_count": water["region_count"],
            "sar_water_regions": water["regions"],
            "overlap_bounds": grid["bounds"],
            "crs": grid["crs"],
            "summary": self._summarize(stats, water),
            "interpretation": (
                "Low SAR backscatter indicates smooth surfaces such as open water, but radar shadow and smooth "
                "tarmac or sand can also appear dark; SAR-only water may be flooding under cloud or flooded vegetation, "
                "optical-only water may be cloud shadow or wet soil."
            ),
        }

        ev = Evidence(
            source_type="fusion",
            source=f"{opt_img.path}, {sar_img.path}",
            tool=self.name,
            bounds=grid["bounds"],
            crs=grid["crs"],
            transform=list(grid["transform"])[:6],
            metadata={k: v for k, v in data.items() if k not in ("summary", "interpretation")},
        )
        return ToolResult(success=True, tool_name=self.name, data=data, evidence=[ev], warnings=warnings)

    @staticmethod
    def _summarize(stats, water):
        if stats["sar_threshold_method"] == "fixed_db":
            rule = f"backscatter below {stats['sar_threshold']} dB"
        else:
            rule = f"backscatter below an automatic threshold of {stats['sar_threshold']} DN"
        parts = [
            f"SAR ({stats['sar_band']}) marks {stats['sar_water_percentage']}% of "
            f"{stats['valid_pixel_count']:,} co-registered pixels as water ({rule})."
        ]
        if water["changed_area_sqm"]:
            parts.append(f"That is approximately {water['changed_area_sqm']:,.0f} m² in {water['region_count']} region(s).")
        if "optical_water_percentage" in stats:
            bands = stats["optical_bands_used"]
            parts.append(
                f"Optical NDWI ({bands['green']}/{bands['nir']}) marks {stats['optical_water_percentage']}% as water; "
                f"the sensors agree on {stats['agreement_percentage']}% of pixels "
                f"({stats['sar_only_water_percentage']}% water in SAR only, "
                f"{stats['optical_only_water_percentage']}% in optical only)."
            )
        return " ".join(parts)
