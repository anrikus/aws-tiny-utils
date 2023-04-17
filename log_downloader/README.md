### What?
This utility downloads logs from AWS CloudWatch Loggroup to a local json.

### Why?
AWS CloudWatch LogInsights has limited download capabilities.

### How?
The utility uses:
- boto3 client to fetch log chunks in temporal order based on the `timestamp_filed_name`,
- merges
- fetches the next chunk based on the last timestamp,
- and finally outputs them to a output json file.

### Setup
- Runtime creation:
```
python3 -m venv log_downloader_venv
source log_downloader_venv/bin/activate
cd aws-tiny-utility/log_downloader_venv
pip install -r requirements.txt
```
- Configure the `runtime_config.toml` with the required parameters.
- Configure your local environment with AWS credentials.
- Make sure the query returns the `timestamp_filed_name` field as configured in `runtime_config.toml`.
- Make sure that the `timestamp_filed_name` is a valid timestamp that can be parsed by `datetime.datetime.fromisoformat()`. The default`@timestamp` is a great choice.
- Make sure the query is sorted by the `timestamp_filed_name` in ascending order.

- Run the utility:
```
python3 log_downloader.py
```

### Limitations
The utility parses the query response and depends on a `timestamp_filed_name` to determine the current state. Hence:
- Correctly configure the `timestamp_filed_name` in the `runtime_config.toml` and ensure that the query returns the field.
- Sort the query results by the `timestamp_filed_name` in ascending order.
- There may be some duplicates which arise due to boto3 client's limitaion of accepting only `int` as `starttime` / `endtime` parameters.