import datajoint as dj
import numpy as np
from scipy import ndimage
from skimage import draw, measure


def path_to_indices(path):
    """From SVG path to numpy array of coordinates, each row being a (row, col) point"""
    indices_str = [
        el.replace("M", "").replace("Z", "").split(",") for el in path.split("L")
    ]
    return np.rint(np.array(indices_str, dtype=float)).astype(int)


def path_to_mask(path, shape):
    """From SVG path to a boolean array where all pixels enclosed by the path
    are True, and the other pixels are False.
    """
    cols, rows = path_to_indices(path).T
    rr, cc = draw.polygon(rows, cols)
    mask = np.zeros(shape, dtype=bool)
    mask[rr, cc] = True
    mask = ndimage.binary_fill_holes(mask)
    return mask


def create_ellipse_mask(vertices, image_shape):
    """
    Create a mask for an ellipse given its vertices.

    :param vertices: Tuple of (x0, y0, x1, y1) representing the bounding box of the ellipse.
    :param image_shape: Shape of the image (height, width) to create a mask for.
    :return: Binary mask with the ellipse.
    """
    x0, x1, y0, y1 = vertices
    center = ((x0 + x1) / 2, (y0 + y1) / 2)
    axis_lengths = (abs(x1 - x0) / 2, abs(y1 - y0) / 2)

    rr, cc = draw.ellipse(
        center[1], center[0], axis_lengths[1], axis_lengths[0], shape=image_shape
    )
    mask = np.zeros(image_shape, dtype=np.bool_)
    mask[rr, cc] = True
    mask = ndimage.binary_fill_holes(mask)

    return mask


def create_rectangle_mask(vertices, image_shape):
    """
    Create a mask for a rectangle given its vertices.

    :param vertices: Tuple of (x0, y0, x1, y1) representing the top-left and bottom-right corners of the rectangle.
    :param image_shape: Shape of the image (height, width) to create a mask for.
    :return: Binary mask with the rectangle.
    """
    x0, x1, y0, y1 = vertices
    rr, cc = draw.rectangle(start=(y0, x0), end=(y1, x1), shape=image_shape)
    mask = np.zeros(image_shape, dtype=np.bool_)
    mask[rr, cc] = True
    mask = ndimage.binary_fill_holes(mask)

    return mask


def create_mask(coordinates, shape_type):
    if shape_type == "path":
        try:
            mask = np.asarray(path_to_mask(coordinates["path"], (512, 512))).nonzero()
        except KeyError:
            for key, info in coordinates.items():
                mask = np.asarray(path_to_mask(info, (512, 512))).nonzero()

    elif shape_type == "circle":
        try:
            mask = np.asarray(
                create_ellipse_mask(
                    [
                        int(coordinates["x0"]),
                        int(coordinates["x1"]),
                        int(coordinates["y0"]),
                        int(coordinates["y1"]),
                    ],
                    (512, 512),
                )
            ).nonzero()
        except KeyError:
            xy_coordinates = np.asarray(
                [item for item in coordinates.values()], dtype="int"
            )
            mask = np.asarray(
                create_ellipse_mask(xy_coordinates, (512, 512))
            ).nonzero()
    elif shape_type == "rect":
        try:
            mask = np.asarray(
                create_rectangle_mask(
                    [
                        int(coordinates["x0"]),
                        int(coordinates["x1"]),
                        int(coordinates["y0"]),
                        int(coordinates["y1"]),
                    ],
                    (512, 512),
                )
            ).nonzero()
        except KeyError:
            xy_coordinates = np.asarray(
                [item for item in coordinates.values()], dtype="int"
            )
            mask = np.asarray(
                create_rectangle_mask(xy_coordinates, (512, 512))
            ).nonzero()
    elif shape_type == "line":
        try:
            mask = np.array(
                (
                    int(coordinates["x0"]),
                    int(coordinates["x1"]),
                    int(coordinates["y0"]),
                    int(coordinates["y1"]),
                )
            )
        except KeyError:
            mask = np.asarray([item for item in coordinates.values()], dtype="int")
    return mask


def get_contours(image_key, prefix):
    scan = dj.create_virtual_module("scan", f"{prefix}scan")
    imaging = dj.create_virtual_module("imaging", f"{prefix}imaging")
    yshape, xshape = (scan.ScanInfo.Field & image_key).fetch1("px_height", "px_width")
    mask_xpix, mask_ypix = (imaging.Segmentation.Mask & image_key).fetch(
        "mask_xpix", "mask_ypix"
    )
    mask_image = np.zeros((yshape, xshape), dtype=bool)
    for xpix, ypix in zip(mask_xpix, mask_ypix):
        mask_image[ypix, xpix] = True
    contours = measure.find_contours(mask_image.astype(float), 0.5)
    return contours


def convert_masks_to_suite2p_format(masks, frame_dims):
    """
    Convert masks to the format expected by Suite2P.

    Parameters:
    masks (list of np.ndarray): A list where each item is an array representing a mask,
                                with non-zero values for the ROI and zeros elsewhere.
    frame_dims (tuple): The dimensions of the imaging frame, (height, width).

    Returns:
    np.ndarray: A 2D array where each column represents a flattened binary mask for an ROI.
    """
    # Calculate the total number of pixels in a frame
    num_pixels = frame_dims[0] * frame_dims[1]
    
    # Initialize an empty array to store the flattened binary masks
    suite2p_masks = np.zeros((num_pixels, len(masks)), dtype=np.float32)
    
    # Convert each mask
    for idx, mask in enumerate(masks):
        # Ensure the mask is binary (1 for ROI, 0 for background)
        binary_mask = np.where(mask > 0, 1, 0).astype(np.float32)
        
        # Flatten the binary mask and add it as a column in the suite2p_masks array
        suite2p_masks[:, idx] = binary_mask.flatten()
    
    return suite2p_masks


def load_imaging_data_for_session(key):
    image_files = (scan.ScanInfo.ScanFile & key).fetch("file_path")
    image_files = [
        find_full_path(get_imaging_root_data_dir(), image_file)
        for image_file in image_files
    ]
    acq_software = (scan.Scan & key).fetch1("acq_software")
    if acq_software == "ScanImage":
        imaging_data =  tifffile.imread(image_files[0])
    elif acq_software == "NIS":
        imaging_data = nd2.imread(image_files[0])
    else:
        raise ValueError(f"Support for images with acquisition software: {acq_software} is not yet implemented into the widget.")
    return imaging_data


def extract_signals_suite2p(key, masks):
    from suite2p.extraction.extract import extrace_traces

    F, _ = extrace_traces(load_imaging_data_for_session(key), masks, neuropil_masks=np.zeros_like(masks))


def insert_signals_into_datajoint(signals, session_key):
    # Implement logic to insert the extracted signals into DataJoint
    pass