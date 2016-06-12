import logging
import numpy as np
from matplotlib.tri import Triangulation
import cv2

# local imports
import pca
from utils.generate_head_texture import fill_triangle, get_colors_triangle, \
    get_row_colors_triangle
import utils.triangles as tu

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)


def get_mean(vector):
    """ construct a mean from a matrix of x,y values
    Args:
        imm_points(numpy array) that follows the following structure:

    Returns:
        mean_values (numpy array)

    Examples:
        Input observations:
            0. [[x_0_0, y_0_0], ... , [x_0_m, y_0_m]],
            1. [[x_1_0, y_1_0], ... , [x_1_m, y_1_m]],
            2. [[x_2_0, y_2_0], ... , [x_2_m, y_2_m]],
            3. [[x_3_0, y_3_0], ... , [x_3_m, y_3_m]]

                ....           ....       .....

            n. [[x_4_0, y_4_0], ... , [x_n_m, y_n_m]]

        This vector containts the mean values of the corresponding column, like so:
            0. [[x_0_0, y_0_0], ... , [x_0_k, y_0_k]],
            1. [[x_1_0, y_1_0], ... , [x_1_k, y_1_k]],
            2. [[x_2_0, y_2_0], ... , [x_2_k, y_2_k]],
            3. [[x_3_0, y_3_0], ... , [x_3_k, y_3_k]]

                ....           ....       .....

            n. [[x_4_0, y_4_0], ... , [x_n_k, y_n_k]]

            mean. [[x_mean_0, y_mean_0], ... [x_mean_n, y_mean_n]]
    """
    return np.mean(vector, axis=0)


def get_triangles(x_vector, y_vector):
    """ perform triangulation between two 2d vectors"""
    return Triangulation(x_vector, y_vector).triangles


def build_shape_feature_vectors(files, get_points, flattened=False):
    """
    Gets the aam points from the files and appends them seperately to one
    array.

    Args:
        files (list): list files

    return:
        list: list of feature vectors
    """
    points = get_points(files)

    if flattened:
        points = pca.flatten_feature_vectors(points, dim=0)

    return points


def sample_from_triangles(src, points2d_src, points2d_dst, triangles):
    # texture = np.asarray(texture, dtype=np.uint8).reshape((-1, 3))
    triangles_pixels = []
    pixels = 0

    for tri in triangles:
        src_p1, src_p2, src_p3 = points2d_src[tri]
        dst_p1, dst_p2, dst_p3 = points2d_dst[tri]

        dst = get_row_colors_triangle(
            src,
            src_p1[0], src_p1[1],
            src_p2[0], src_p2[1],
            src_p3[0], src_p3[1],
            dst_p1[0], dst_p1[1],
            dst_p2[0], dst_p2[1],
            dst_p3[0], dst_p3[1]
        )

        pixels += dst.flatten().shape[0]

        triangles_pixels.extend(dst.flatten())

    result = np.asarray(triangles_pixels, dtype=np.uint8)

    return result


def build_texture_feature_vectors(files, get_image_with_shape, mean_shape, triangles):
    """
    Args:
        files (list): list files
        flattened (bool): Flatten the inner feature vectors, see
            flatten_feature_vectors.

    Returns:
        list: list of feature vectors
    """
    mean_texture = []

    mean_shape_scaled = mean_shape.reshape((58, 2))
    mean_shape_scaled[:, 0] = mean_shape_scaled[:, 0] * 640
    mean_shape_scaled[:, 1] = mean_shape_scaled[:, 1] * 480

    for i, f in enumerate(files):
        image, shape = get_image_with_shape(f)
        h, w, c = image.shape

        shape[:, 0] = shape[:, 0] * w
        shape[:, 1] = shape[:, 1] * h

        triangles_colors = sample_from_triangles(
            image, shape, mean_shape_scaled, triangles
            )

        mean_texture.append(triangles_colors)
        logger.info('processed file: {} {}/{}'.format(f, i, len(files)))

        # cv2.imshow('image', image)
        # k = cv2.waitKey(0) & 0xFF

        # if k == 27:
        #     break
    mean_texture = np.asarray(mean_texture)
    #mean_texture = pca.flatten_feature_vectors(mean_texture)

    return mean_texture


def get_pixel_values(image, points):
    h, w, c = image.shape

    points[:, 0] = points[:, 0] * w
    points[:, 1] = points[:, 1] * h

    image = cv2.blur(image, (3, 3))

    hull = cv2.convexHull(points, returnPoints=True)
    rect = cv2.boundingRect(hull)

    x, y, w, h = rect

    # pixels = np.zeros((h, w, c), dtype=np.uint8)
    for i in np.linspace(0, 1, num=150):
        for j in np.linspace(0, 1, num=150):
            y_loc_g = int(i * h + y)
            x_loc_g = int(j * w + x)

            if cv2.pointPolygonTest(hull, (x_loc_g, y_loc_g), measureDist=False) >= 0:
                image[y_loc_g][x_loc_g][0] = 0
                image[y_loc_g][x_loc_g][1] = 0
                image[y_loc_g][x_loc_g][2] = 0

    # return np.asarray(pixels, dtype=np.uint8), hull
    return image, hull
