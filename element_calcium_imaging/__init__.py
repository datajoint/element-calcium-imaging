import datajoint as dj
import pathlib

dj.config['enable_python_native_blobs'] = True


def find_full_path(root_directories, relative_path):
    """
    Given a relative path, search and return the full-path
     from provided potential root directories (in the given order)
        :param root_directories: potential root directories
        :param relative_path: the relative path to find the valid root directory
        :return: root_directory (pathlib.Path object)
    """
    relative_path = pathlib.Path(relative_path)
    
    # If the relative_path is an absolute path
    if relative_path.exists():
        return relative_path

    # turn to list if only a single root directory is provided
    if isinstance(root_directories, (str, pathlib.Path)):
        root_directories = [root_directories]

    for root_dir in root_directories:
        if (pathlib.Path(root_dir) / relative_path).exists():
            return pathlib.Path(root_dir) / relative_path

    raise FileNotFoundError('No valid full-path found (from {})'
                            ' for {}'.format(root_directories, relative_path))


def find_root_directory(root_directories, full_path):
    """
    Given multiple potential root directories and a full-path,
    search and return one directory that is the parent of the given path
        :param root_directories: potential root directories
        :param full_path: the relative path to search the root directory
        :return: full-path (pathlib.Path object)
    """
    full_path = pathlib.Path(full_path)

    if not full_path.exists():
        raise FileNotFoundError(f'{full_path} does not exist!')

    # turn to list if only a single root directory is provided
    if isinstance(root_directories, (str, pathlib.Path)):
        root_directories = [root_directories]

    try:
        return next(pathlib.Path(root_dir) for root_dir in root_directories
                    if pathlib.Path(root_dir) in set(full_path.parents))
    except StopIteration:
        raise FileNotFoundError('No valid root directory found (from {})'
                                ' for {}'.format(root_directories, full_path))
