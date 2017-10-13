import folium
import geojson
import matplotlib.pyplot as plt
import numpy as np

from remotesensing.tools import gis


class Visualise:
    """ Class for visualising geospatial data"""
    @staticmethod
    def image_bounds(image_list):
        """ Display image boundary on a slippy Leaflet map
        :type image_list: list[image.Image]
        :rtype: folium.Map
        """
        unprojected_bounds = [gis.transform_polygon(image.bounds,
                                                    in_epsg=image.epsg,
                                                    out_epsg=gis.WGS84_EPSG) for image in image_list]
        geojson_bounds = [geojson.Feature(geometry=bounds) for bounds in unprojected_bounds]
        center = unprojected_bounds[0].centroid.xy
        map_window = folium.Map(location=[center[1][0], center[0][0]])
        for boundary in geojson_bounds:
            folium.GeoJson(boundary).add_to(map_window)

        return map_window

    @staticmethod
    def search_results(scene_list):
        """ Display a list of satellite scenes on a slippy Leaflet map
        :type scene_list: list[cloud.scene.SatelliteScene]
        :rtype: folium.Map
        """
        map_window = folium.Map()
        for scene in scene_list:
            scene_geojson = geojson.Feature(geometry=scene.bounds)
            folium.GeoJson(
                scene_geojson,
                style_function=lambda feature: {
                    'fillOpacity': 0,
                }).add_to(map_window)

        return map_window

    @staticmethod
    def save_pyplot(image: np.ndarray, filepath, width_in_pixels, height_in_pixels, dpi=72):
        """ Plot an image and save it without whitespace
        :type image: numpy.ndarray
        :type filepath: str
        :type width_in_pixels: int
        :type height_in_pixels: int
        :type dpi: int
        """
        f = plt.figure(frameon=False, dpi=dpi)
        f.set_size_inches(width_in_pixels/dpi, height_in_pixels/dpi)

        ax = plt.Axes(f, [0., 0., 1., 1.])
        ax.set_axis_off()
        f.add_axes(ax)

        ax.imshow(image, aspect='normal')
        f.savefig(filepath, dpi=dpi)

    @staticmethod
    def show_3d_surface(image, figsize=(15, 10), rstride=100, cstride=100, cmap='jet'):
        """ Plots a 2D image as a surface model
        :type image: image.Image
        :type figsize: tuple(int, int)
        :type rstride: int
        :type cstride: int
        :type cmap: str
        """
        if image.band_count > 1:
            raise UserWarning("Image must be 2D")

        xx, yy = np.mgrid[0:image.width, 0:image.height]

        f = plt.figure(figsize=figsize)
        ax = f.gca(projection='3d')

        ax.plot_surface(xx, yy, image.pixels, rstride=rstride, cstride=cstride, cmap=cmap, linewidth=0)
        plt.show()

    @staticmethod
    def show_superpixel_spectra(superpixels):
        """ Plot the average spectra for each superpixel cluster
        :type superpixels: classify.superpixel.Superpixels
        """
        plt.figure(figsize=(15, 10))

        for cluster in superpixels.gdf.cluster.unique():
            features = np.stack(superpixels.gdf.loc[superpixels.gdf.cluster == cluster].features.tolist())
            mean = np.nanmean(features, axis=0)
            std = np.nanmean(features, axis=0)

            plt.plot(mean, label=cluster)
            plt.fill_between([x for x in range(len(mean))], mean-std, mean=std, alpha=0.2)

        plt.legend()
        plt.show()
