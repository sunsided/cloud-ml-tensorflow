from os import path
from glob import iglob
from tqdm import tqdm
from typing import Dict, Optional

import csv
from hashlib import sha256
from random import random

from google.cloud import storage
from oauth2client.client import GoogleCredentials


def main():
    bucket_name = 'research-and-development'
    bucket = _get_bucket(bucket_name)

    dict_filename = 'dict.txt'
    all_filename = 'all_data.csv'
    train_filename = 'train_set.csv'
    eval_filename = 'eval_set.csv'

    object_dir = 'cloud-ml/mmayer/kotaru'  # Koffer, Tasche, Rucksack

    source_dir = 'augmented'
    classes_map = _get_classes_from_dir(source_dir)

    # write the class dictionary
    with open(dict_filename, 'w') as f:
        for class_name in classes_map.keys():
            f.write(class_name + '\n')

    # upload the files and register the class labels
    with open(all_filename, 'w', newline="\n", encoding="utf-8") as fc, \
            open(train_filename, 'w', newline='\n', encoding='utf-8') as ft, \
            open(eval_filename, 'w', newline='\n', encoding='utf-8') as fe, \
            open('file_map.tsv', 'w', newline='\n', encoding='utf-8') as fm:
        all_writer = csv.writer(fc, delimiter=',')
        train_writer = csv.writer(ft, delimiter=',')
        eval_writer = csv.writer(fe, delimiter=',')
        map_writer = csv.writer(fm, delimiter='\t')

        for (class_name, dir) in tqdm(classes_map.items(), desc='Total progress'):
            file_pattern = path.join(dir, '*.*')
            files = (name for name in iglob(file_pattern) if path.isfile(name))
            for file in tqdm(files, desc='Class \'%s\'' % class_name):
                target_filename = sha256(path.basename(file).encode('utf-8')).hexdigest()

                blob_name = '%s/%s/%s.jpg' % (object_dir, class_name, target_filename)
                blob_url = 'gs://%s/%s' % (bucket_name, blob_name)

                _upload_to_gs(file, blob_name, bucket)

                all_writer.writerow([blob_url, class_name])
                if random() >= 0.3:
                    train_writer.writerow([blob_url, class_name])
                else:
                    eval_writer.writerow([blob_url, class_name])

                map_writer.writerow([blob_url, file])

            fc.flush()
            fm.flush()

        # upload all the things!
        for file_name in [dict_filename, all_filename, train_filename, eval_filename]:
            _upload_to_gs(file_name, '%s/%s' % (object_dir, file_name), bucket)


def _get_classes_from_dir(source_dir: str) -> Dict[str, str]:
    classes = {}
    dir_pattern = path.join(source_dir, '*')
    directories = (name for name in iglob(dir_pattern) if path.isdir(name))
    for class_dir in directories:
        class_name = path.basename(class_dir)
        classes[class_name] = class_dir
    return classes


def _get_bucket(bucket_name: str, credentials_file: str='google-credentials.json') -> storage.Bucket:
    credentials = GoogleCredentials.from_stream(credentials_file)
    assert credentials is not None
    storage_client = storage.Client()
    return storage_client.get_bucket(bucket_name)


def _upload_to_gs(local_file_path: str, blob_name: str, bucket: storage.Bucket):
    assert path.exists(local_file_path)

    blob = bucket.blob(blob_name)
    assert blob is not None

    blob.upload_from_filename(local_file_path)

    blob.metadata = {'origin': local_file_path}
    blob.patch()


if __name__ == "__main__":
    main()
