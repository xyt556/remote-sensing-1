from remotesensing.image import Image
from remotesensing.image import Geotransform
from remotesensing.tools import gis

from typing import Dict
from shapely.geometry import Polygon
from osgeo import gdal, osr


class Loader:
    def load(self, file_path: str, band_labels: Dict[str, int] = None, extent: Polygon = None) -> Image:

        if extent:
            return self.load_from_dataset_and_clip(gdal.Open(file_path), band_labels, extent)
        else:
            return self.load_from_dataset(gdal.Open(file_path), band_labels)

    def load_from_dataset_and_clip(self, image_dataset: gdal.Dataset, band_labels: Dict, extent: Polygon) -> Image:

        geo_transform = self._load_geotransform(image_dataset)
        projection = image_dataset.GetProjection()
        epsg = osr.SpatialReference(wkt=projection).GetAttrValue("AUTHORITY", 1)
        pixel_polygon = gis.polygon_to_pixel(gis.transform_polygon(extent, in_epsg=4326, out_epsg=epsg), geo_transform)

        bounds = [int(bound) for bound in pixel_polygon.bounds]

        pixels = image_dataset.ReadAsArray(bounds[0], bounds[1], bounds[2]-bounds[0], bounds[3]-bounds[1])
        geo_transform = gis.subset_geotransform(geo_transform, bounds[0], bounds[1])
        pixel_polygon = gis.polygon_to_pixel(gis.transform_polygon(extent, in_epsg=4326, out_epsg=epsg), geo_transform)

        if pixels.ndim > 2:
            pixels = pixels.transpose(1, 2, 0)

        return Image(pixels, geo_transform, projection, band_labels=band_labels).clip_with(pixel_polygon, mask_value=0)

    def load_from_dataset(self, image_dataset: gdal.Dataset, band_labels: Dict = None) -> Image:

        geo_transform = self._load_geotransform(image_dataset)
        projection = image_dataset.GetProjection()
        pixels = image_dataset.ReadAsArray()

        if pixels.ndim > 2:
            pixels = pixels.transpose(1, 2, 0)

        return Image(pixels, geo_transform, projection, band_labels=band_labels)

    def _load_geotransform(self, image_dataset: gdal.Dataset) -> Geotransform:

        return Geotransform(image_dataset.GetGeoTransform())
