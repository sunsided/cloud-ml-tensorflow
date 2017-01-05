import os
from os import path
from glob import iglob
from argparse import ArgumentParser
from PIL import Image
from tqdm import tqdm
import numpy as np


def ensure_dir(name):
    if not path.exists(name):
        os.makedirs(name)


def alpha_composite(src, dst):
    """
    Return the alpha composite of src and dst.

    Parameters:
    src -- PIL RGBA Image object
    dst -- PIL RGBA Image object

    The algorithm comes from http://en.wikipedia.org/wiki/Alpha_compositing
    """
    # http://stackoverflow.com/a/9166671/195651
    # http://stackoverflow.com/a/3375291/190597
    # http://stackoverflow.com/a/9166671/190597
    src = np.asarray(src)
    dst = np.asarray(dst)
    out = np.empty(src.shape, dtype='float')
    alpha = np.index_exp[:, :, 3:]
    rgb = np.index_exp[:, :, :3]
    src_a = src[alpha] / 255.
    dst_a = dst[alpha] / 255.
    out[alpha] = src_a + dst_a*(1 - src_a)
    old_setting = np.seterr(invalid='ignore')
    out[rgb] = (src[rgb]*src_a + dst[rgb]*dst_a*(1. - src_a))/out[alpha]
    np.seterr(**old_setting)
    out[alpha] *= 255
    np.clip(out, 0, 255)
    # astype('uint8') maps np.nan (and np.inf) to 0
    out = out.astype('uint8')
    out = Image.fromarray(out, 'RGBA')
    return out


def saveas(image, target_dir, name, quality=98):
    target_name = path.join(target_dir, name + '.jpg')
    image.save(target_name, quality=quality)


def resize_with_aspect(image, target_width, target_height):
    width = int(target_width)
    height = int(target_height)
    image_aspect = float(image.width) / float(image.height)
    new_aspect = float(width) / float(height)
    if image_aspect < new_aspect:
        height = int(width / image_aspect)
    else:
        width = int(height * image_aspect)

    return image.resize((width, height), resample=Image.ANTIALIAS)


def main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--src', dest='src_dir', metavar='DIR', type=str, required=True,
                        help='The source directory')
    parser.add_argument('-d', '--dst', dest='dst_dir', metavar='DIR', type=str, required=True,
                        help='The destination directory')
    parser.add_argument('-W', '--width', dest='width', metavar='WIDTH', type=int, default=299,
                        help='The resized image\'s width')
    parser.add_argument('-H', '--height', dest='height', metavar='HEIGHT', type=int, default=299,
                        help='The resized image\'s height')
    args = parser.parse_args()

    source_dir = args.src_dir
    dest_dir = args.dst_dir
    target_width = args.width
    target_height = args.height#
    target_area = target_width * target_height

    if not os.path.exists(source_dir):
        parser.error('The source directory does not exist: %s' % source_dir)

    ensure_dir(dest_dir)

    dirmap = {}

    dir_pattern = path.join(source_dir, '*')
    directories = (name for name in iglob(dir_pattern) if path.isdir(name))
    for source in directories:
        target = path.join(dest_dir, path.basename(source).lower())
        dirmap[source] = target
        ensure_dir(target)

    file_pattern = path.join(source_dir, '**', '*.*')
    files = (name for name in iglob(file_pattern) if path.isfile(name))

    for (source, image) in tqdm((source, Image.open(source, 'r')) for source in files):
        basename = path.splitext(path.basename(source))[0]

        target_dir = dirmap[path.dirname(source)]

        # render alpha-transparent images onto white background
        if 'A' in image.mode:
            image.load()

            white = Image.new('RGBA', image.size, (255, 255, 255, 255))
            composite = alpha_composite(image, white)

            image.close()
            image = composite

        image = image.convert('RGB')
        original_area = image.width * image.height

        # TODO: slightly angle, then crop the center
        # TODO: perspective distortion
        # TODO: Mask out random parts of the image by overlaying with randomly placed synthetic features
        # TODO: Superimpose image onto colorful background

        # simple resize
        resized = image.resize((target_width, target_height), resample=Image.ANTIALIAS)
        saveas(resized, target_dir, basename, quality=98)

        if (original_area <= (target_area * 1.1)) or (image.width == image.height):
            continue

        # zoom-crop the center
        resized = resize_with_aspect(image, target_width * 1.1, target_height * 1.1)
        top = int((resized.height - target_height) / 2)
        left = int((resized.width - target_width) / 2)
        cropped = resized.crop((left, top, left + target_width, top + target_height))
        saveas(cropped, target_dir, basename + '-centercrop', quality=98)


if __name__ == "__main__":
    main()
