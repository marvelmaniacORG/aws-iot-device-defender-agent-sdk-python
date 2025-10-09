import awsiot.greengrasscoreipc
import logging
import os
import psutil as ps
from time import sleep
from AWSIoTDeviceDefenderAgentSDK import collector
from awsiot.greengrasscoreipc.model import PublishToIoTCoreRequest, QOS

MIN_INTERVAL_SECONDS = 300

# Configure logging
logger = logging.getLogger("AWSIoTPythonSDK.core")
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

ipc_client = awsiot.greengrasscoreipc.connect()


def publish_metrics():
    try:
        # You will need to use Local Resource Access to map the hosts /proc to a directory accessible in the lambda
        ps.PROCFS_PATH = os.environ.get("PROCFS_PATH", "/proc")
        core_name = os.environ.get("AWS_IOT_THING_NAME", "unknown-device")
        topic = "$aws/things/" + core_name + "/defender/metrics/json"

        interval_str = os.environ.get(
            "SAMPLE_INTERVAL_SECONDS", str(MIN_INTERVAL_SECONDS)
        )
        sample_interval_seconds = int(interval_str)
        if sample_interval_seconds < MIN_INTERVAL_SECONDS:
            sample_interval_seconds = MIN_INTERVAL_SECONDS

        print("Collector running on device: " + core_name)
        print("Metrics topic: " + topic)
        print("Sampling interval: " + str(sample_interval_seconds) + " seconds")

        metrics_collector = collector.Collector(short_metrics_names=False)

        while True:
            metric = metrics_collector.collect_metrics()

            request = PublishToIoTCoreRequest()
            request.topic_name = topic
            request.payload = bytes(metric.to_json_string(), "utf-8")
            request.qos = QOS.AT_LEAST_ONCE

            operation = ipc_client.new_publish_to_iot_core()
            operation.activate(request)
            future = operation.get_response()
            future.result(timeout=10.0)

            sleep(float(sample_interval_seconds))

    except Exception as e:
        print("Error: " + str(e))
        return


def function_handler(event, context):
    print("Lambda got event: " + str(event) + " context:" + str(context))


# Kickstart the long-running lambda publisher
publish_metrics()
