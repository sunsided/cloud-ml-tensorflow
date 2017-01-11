# Readme

## Setup

Follow the instructions provided [on this page](https://cloud.google.com/ml/docs/how-tos/getting-set-up)
following the local installation path.

Check the environment using

```bash
curl https://raw.githubusercontent.com/GoogleCloudPlatform/cloudml-samples/master/tools/check_environment.py | python
```

Don't forget to (once!) activate Cloud ML for the project
by issuing

```bash
gcloud beta ml init-project
```

You can tell you didn't when you encounter an error message like

```
ERROR: (gcloud.beta.ml.jobs.submit.training) FAILED_PRECONDITION: Field: package_uris Error: The provided GCS paths [gs://bucket/path/file.tar.gz] cannot be read by service account cloud-ml-service@project-id-aa9b7.iam.gserviceaccount.com.
```

## Training run

The training requires the actual training task (`trainer/task.py`) to be available as the specified module.
Note that the `__init__.py` file is required but might be empty.

Then the training job is run on the TFRecord files available in the object storage:

```bash
gcloud beta ml jobs submit training \
    kotaru_v3 \
    --module-name trainer.task \
    --package-path trainer \
    --staging-bucket "gs://research-and-development" \
    --region europe-west1 \
    -- \
    --output_path "gs://research-and-development/cloud-ml/mmayer/kotaru/training" \
    --eval_data_paths "gs://research-and-development/cloud-ml/mmayer/kotaru/preproc/eval*" \
    --train_data_paths "gs://research-and-development/cloud-ml/mmayer/kotaru/preproc/train*"
```

Create the model and the initial version:

```bash
MODEL_NAME=kotaru
VERSION_NAME=v1
gcloud beta ml models create ${MODEL_NAME}
gcloud beta ml versions create \
    --origin gs://research-and-development/cloud-ml/mmayer/kotaru/training/model/ \
    --model $MODEL_NAME \
    $VERSION_NAME
```

Create an example request:

```bash
python -c "import base64, sys, json; img = base64.b64encode(open(sys.argv[1], 'rb').read()); print json.dumps({'key':'0', 'image_bytes': {'b64': img}})" augmented/koffer/0.jpg > request.json
```

This results in a `request.json` that looks like this:

```json
{"image_bytes": {"b64": "/9j/4AAQSkZJRgA...KACiiigAooooAKKKKACiiigD//Z"}, "key": "0"}
```

