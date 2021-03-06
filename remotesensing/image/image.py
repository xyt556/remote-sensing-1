import numpy as np
from scipy import ndimage
from typing import List, Tuple
from osgeo import gdal, osr
from tqdm import tqdm

from remotesensing.tools import gis
from remotesensing.image import Geotransform
from remotesensing.geometry import GeoPolygon

GTIFF_DRIVER = 'GTiff'


class Image:
    """ A generic image object using gdal with shape (y, x, band) """
    def __init__(self, pixels: np.ndarray, geotransform: Geotransform, projection: str):

        self.pixels = pixels
        self.data_type = self.pixels.dtype
        self.geotransform = geotransform
        self.projection = projection

    def __repr__(self) -> str:

        return f'Image - Shape: {self.width}x{self.height}x{self.band_count} | EPSG: {self.epsg}'

    def __getitem__(self, image_slice) -> "Image":

        geo_transform = self.geotransform

        if type(image_slice) is tuple:
            pixels = self.pixels[image_slice]

            if len(image_slice) > 1:
                x, y = image_slice[1].start, image_slice[0].start
                if x is None:
                    x = 0
                if y is None:
                    y = 0
                geo_transform = self.geotransform.subset(x, y)

            return Image(pixels, geo_transform, self.projection)

    def _get_band_by_number(self, band_number: int) -> np.ndarray:

        return self.pixels[:, :, band_number-1]

    @property
    def width(self) -> int:

        return self.pixels.shape[0]

    @property
    def height(self) -> int:

        return self.pixels.shape[1]

    @property
    def band_count(self) -> int:

        if self.pixels.ndim > 2:
            return self.pixels.shape[2]
        else:
            return 1

    @property
    def shape(self) -> Tuple[int]:

        return self.pixels.shape

    @property
    def dtype(self) -> str:

        return self.pixels.dtype

    @property
    def epsg(self) -> int:

        spatial_reference = osr.SpatialReference(wkt=self.projection)
        return spatial_reference.GetAttrValue("AUTHORITY", 1)

    def clip_with(self, polygon: GeoPolygon, mask_value: float = np.nan) -> "Image":

        return gis.clip_image(self, polygon.polygon, mask_value=mask_value)

    def upsample(self, factor: int) -> "Image":

        resampled_pixels = ndimage.zoom(self.pixels, factor, order=0)
        scaled_geo_transform = self.geotransform.scale(factor)

        return Image(resampled_pixels, scaled_geo_transform, self.projection)

    def apply(self, function: callable) -> "Image":

        modified_pixels = function(self.pixels)
        return Image(modified_pixels, self.geotransform, self.projection)

    @staticmethod
    def stack(images: List["Image"]) -> "Image":

        if len(images) == 1:
            raise UserWarning("Only one image has been provided")
        else:
            stack = np.zeros((images[0].width, images[0].height, sum([image.band_count for image in images])))

            band_count = 0
            for image in tqdm(images, total=len(images), desc='Stacking bands'):
                if image.band_count > 1:
                    for i in range(image.band_count):
                        stack[:, :, band_count] = image[:, :, i].pixels
                else:
                    stack[:, :, band_count] = image.pixels
                band_count += 1

            return Image(stack, images[0].geotransform, images[0].projection)

    def save(self, file_path: str, data_type: str = 'uint16'):

        gdal_data_type = self._get_gdal_data_type(data_type)
        out_image = gdal.GetDriverByName(GTIFF_DRIVER)\
            .Create(file_path, self.height, self.width, self.band_count, gdal_data_type)
        out_image.SetGeoTransform(self.geotransform.tuple)
        out_image.SetProjection(self.projection)

        if self.band_count > 1:
            for band in range(self.band_count):
                out_image.GetRasterBand(band+1).WriteArray(self.pixels[:, :, band])
        else:
            out_image.GetRasterBand(1).WriteArray(self.pixels)

        out_image.FlushCache()

    @property
    def normalise(self) -> "Image":
        """ normalise image to 0-1 """

        image_min, image_max = np.nanmin(self.pixels), np.nanmax(self.pixels)
        return self.apply(lambda x: (x - image_min) / (image_max - image_min))

    def add_index(self, band_1: int, band_2: int) -> "Image":

        if self.band_count == 1:
            raise UserWarning(f'Image only has one band')

        for band in [band_1, band_2]:
            if self.band_count < band:
                raise UserWarning(f'Band number: {band} greater than image bands: {self.band_count}')

        band_1_pixels = self.pixels[:, :, band_1]
        band_2_pixels = self.pixels[:, :, band_2]

        index = (band_1_pixels - band_2_pixels) / (band_1_pixels + band_2_pixels)

        return Image(np.dstack([self.pixels, index]), self.geotransform, self.projection)

    @staticmethod
    def _get_gdal_data_type(name: str):
        if name == 'uint8':
            return gdal.GDT_Byte
        elif name == 'uint16':
            return gdal.GDT_UInt16
        elif name == 'float32':
            return gdal.GDT_Float32
        else:
            raise UserWarning("Unrecognised data type.")
