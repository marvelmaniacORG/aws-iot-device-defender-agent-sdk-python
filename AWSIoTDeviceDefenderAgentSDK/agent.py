# Copyright 2025 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License").
#   You may not use this file except in compliance with the License.
#   A copy of the License is located at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   or in the "license" file accompanying this file. This file is distributed
#   on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
#   express or implied. See the License for the specific language governing
#   permissions and limitations under the License.


from awscrt import io, mqtt5, auth, http
from awsiot import mqtt5_client_builder
from AWSIoTDeviceDefenderAgentSDK import collector
import logging
import argparse
from time import sleep
from socket import gethostname
import cbor2 as cbor
import sys

# Set up logging
logger = logging.getLogger(__name__)


class IoTClientWrapper(object):
    """
    Wrapper around the AWS Iot Python SDK.

    Sets common parameters based on the AWS Iot Python SDK's `Basic PubSub`_ sample.

    .. _Basic PubSub: https://github.com/aws/aws-iot-device-sdk-python-v2/blob/main/samples/pubsub.py

    """

    def __init__(
        self,
        endpoint,
        root_ca_path,
        certificate_path,
        private_key_path,
        client_id,
        signing_region,
        proxy_host,
        proxy_port,
        use_websocket,
    ):
        self.host = endpoint
        self.root_ca_path = root_ca_path
        self.certificate_path = certificate_path
        self.private_key_path = private_key_path
        self.client_id = client_id
        self.signing_region = signing_region
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.use_websocket = use_websocket
        self.iot_client = None
        self.topic_callbacks = {}

    def on_publish_received(self, publish_packet_data):
        """Handle incoming MQTT 5.0 messages"""
        topic = publish_packet_data.publish_packet.topic
        payload = publish_packet_data.publish_packet.payload

        logger.debug(f"Received message on topic: {topic}")
        logger.debug(f"Payload size: {len(payload) if payload else 0} bytes")

        # Find matching callback for this topic
        callback_found = False
        for subscribed_topic, callback in self.topic_callbacks.items():
            if topic == subscribed_topic:
                logger.debug(
                    f"Routing message to callback for topic: {subscribed_topic}"
                )
                try:
                    callback(topic, payload)
                    callback_found = True
                except Exception as e:
                    logger.error(f"Error in callback for topic {topic}: {e}")
                break

        if not callback_found:
            logger.warning(f"No callback found for topic: {topic}")

    def publish(self, publish_to_topic, payload):
        """Publish to MQTT 5.0"""
        logger.debug(f"Publishing to topic: {publish_to_topic}")
        logger.debug(f"Payload size: {len(payload) if payload else 0} bytes")

        try:
            publish_packet = mqtt5.PublishPacket(
                topic=publish_to_topic, payload=payload, qos=mqtt5.QoS.AT_MOST_ONCE
            )
            publish_future = self.iot_client.publish(publish_packet)
            logger.debug(f"Publish request sent for topic: {publish_to_topic}")
            return publish_future
        except Exception as e:
            logger.error(f"Failed to publish to topic {publish_to_topic}: {e}")
            raise

    def subscribe(self, subscribe_to_topic, callback):
        """Subscribe to MQTT 5.0"""
        logger.info(f"Subscribing to topic: {subscribe_to_topic}")

        try:
            # Store callback for this topic
            self.topic_callbacks[subscribe_to_topic] = callback
            logger.debug(f"Callback registered for topic: {subscribe_to_topic}")

            subscribe_packet = mqtt5.SubscribePacket(
                subscriptions=[
                    mqtt5.Subscription(
                        topic_filter=subscribe_to_topic, qos=mqtt5.QoS.AT_LEAST_ONCE
                    )
                ]
            )

            subscribe_future = self.iot_client.subscribe(
                subscribe_packet=subscribe_packet
            )
            subscribe_result = subscribe_future.result()

            reason_code = subscribe_result.reason_codes[0]
            logger.info(
                f"Successfully subscribed to {subscribe_to_topic} with QoS: {reason_code}"
            )

            return subscribe_result
        except Exception as e:
            logger.error(f"Failed to subscribe to topic {subscribe_to_topic}: {e}")
            raise

    def connect(self):
        """Connect to AWS IoT"""
        logger.info(f"Initiating connection to AWS IoT endpoint: {self.host}")
        logger.info(f"Client ID: {self.client_id}")
        logger.debug(f"Using websocket: {self.use_websocket}")

        if not self.certificate_path or not self.private_key_path:
            logger.error("Missing credentials for authentication")

            exit(2)

        logger.debug("Certificate path: %s", self.certificate_path)
        logger.debug("Private key path: %s", self.private_key_path)
        logger.debug("Root CA path: %s", self.root_ca_path)

        try:
            # Spin up resources
            logger.debug("Creating AWS CRT resources")
            event_loop_group = io.EventLoopGroup(1)
            host_resolver = io.DefaultHostResolver(event_loop_group)
            client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
        except Exception as e:
            logger.error(f"Failed to create AWS CRT resources: {e}")
            raise

        if self.use_websocket is True:
            logger.info("Using WebSocket connection with AWS Signature V4")
            logger.debug(f"Signing region: {self.signing_region}")

            proxy_options = None
            if self.proxy_host:
                logger.info(f"Using proxy: {self.proxy_host}:{self.proxy_port}")
                proxy_options = http.HttpProxyOptions(
                    host_name=self.proxy_host, port=self.proxy_port
                )

            try:
                credentials_provider = auth.AwsCredentialsProvider.new_default_chain(
                    client_bootstrap
                )
                logger.debug("Created AWS credentials provider")

                self.iot_client = (
                    mqtt5_client_builder.websockets_with_default_aws_signing(
                        endpoint=self.host,
                        client_bootstrap=client_bootstrap,
                        region=self.signing_region,
                        credentials_provider=credentials_provider,
                        http_proxy_options=proxy_options,
                        ca_filepath=self.root_ca_path,
                        on_publish_received=self.on_publish_received,
                        client_id=self.client_id,
                        clean_start=False,
                        keep_alive_interval_seconds=30,
                    )
                )
                logger.info("WebSocket MQTT 5.0 client created successfully")
            except Exception as e:
                logger.error(f"Failed to create WebSocket MQTT client: {e}")
                raise

        else:
            logger.info("Using mTLS connection with X.509 certificates")
            try:
                self.iot_client = mqtt5_client_builder.mtls_from_path(
                    endpoint=self.host,
                    cert_filepath=self.certificate_path,
                    pri_key_filepath=self.private_key_path,
                    client_bootstrap=client_bootstrap,
                    ca_filepath=self.root_ca_path,
                    on_publish_received=self.on_publish_received,
                    client_id=self.client_id,
                    clean_start=False,
                    keep_alive_interval_seconds=30,
                )
                logger.info("mTLS MQTT 5.0 client created successfully")
            except Exception as e:
                logger.error(f"Failed to create mTLS MQTT client: {e}")
                raise

        logger.info(f"Starting MQTT 5.0 client connection to {self.host}")

        try:
            # Start the MQTT 5.0 client
            self.iot_client.start()
            logger.debug("MQTT 5.0 client started successfully")
            sleep(2)
            logger.info("Connection established successfully")
        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")
            raise


def parse_args():
    """Setup Commandline Argument Parsing"""
    parser = argparse.ArgumentParser(fromfile_prefix_chars="@")
    parser.add_argument(
        "-e",
        "--endpoint",
        action="store",
        required=True,
        dest="endpoint",
        help="Your AWS IoT custom endpoint, not including a port. "
        + 'Ex: "abcd123456wxyz-ats.iot.us-east-1.amazonaws.com"',
    )
    parser.add_argument(
        "-r",
        "--rootCA",
        action="store",
        dest="root_ca_path",
        required=True,
        help="File path to root certificate authority, in PEM format. "
        + "Necessary if MQTT server uses a certificate that's not already in "
        + "your trust store.",
    )
    parser.add_argument(
        "-c",
        "--cert",
        action="store",
        dest="certificate_path",
        required=True,
        help="File path to your client certificate, in PEM format.",
    )
    parser.add_argument(
        "-k",
        "--key",
        action="store",
        dest="private_key_path",
        required=True,
        help="File path to your private key, in PEM format.",
    )
    parser.add_argument(
        "-id",
        "--client_id",
        action="store",
        dest="client_id",
        required=True,
        help="MQTT Client id, used as thing name for metrics, unless one is passed as a parameter",
    )
    parser.add_argument(
        "-w",
        "--use-websocket",
        action="store",
        dest="use_websocket",
        default=False,
        help="To use a websocket instead of raw mqtt. If you "
        + "specify this option you must specify a region for signing, you can also enable proxy mode.",
    )
    parser.add_argument(
        "-se",
        "--signing-region",
        action="store",
        dest="signing_region",
        default="us-east-1",
        help="If you specify --use-web-socket, this "
        + "is the region that will be used for computing the Sigv4 signature",
    )
    parser.add_argument(
        "-t",
        "--thing_name",
        action="store",
        dest="thing_name",
        required=False,
        help="Thing to publish metrics for. If omitted, client_id is assumed",
    )
    parser.add_argument(
        "-d",
        "--dryrun",
        action="store_true",
        dest="dry_run",
        default=False,
        help="Collect and print metrics to console, do not publish them over mqtt",
    )
    parser.add_argument(
        "-i",
        "--interval",
        action="store",
        dest="upload_interval",
        default=300,
        help="Interval in seconds between metric uploads",
    )
    parser.add_argument(
        "-s",
        "--short_tags",
        action="store_true",
        dest="short_tags",
        default=False,
        help="Use long-format field names in metrics report",
    )
    parser.add_argument(
        "-f",
        "--format",
        action="store",
        dest="format",
        required=True,
        choices=["cbor", "json"],
        default="json",
        help="Choose serialization format for metrics report",
    )
    parser.add_argument(
        "-ph",
        "--proxy-host",
        action="store",
        dest="proxy_host",
        help="Hostname for proxy to connect to. Note: if you use this feature, "
        + "you will likely need to set --root-ca to the ca for your proxy.",
    )
    parser.add_argument(
        "-pp",
        "--proxy-port",
        action="store",
        dest="proxy_port",
        type=int,
        default=8080,
        help="Port for proxy to connect to.",
    )
    parser.add_argument(
        "--verbosity",
        action="store",
        dest="verbosity",
        choices=[x.name for x in io.LogLevel],
        default=io.LogLevel.NoLogs.name,
        help="Logging level",
    )
    parser.add_argument(
        "-cm",
        "--include-custom-metrics",
        "--custom-metrics",
        action="store_true",
        dest="custom_metrics",
        default=False,
        help="Adds custom metrics to payload.",
    )
    return parser.parse_args()


def custom_callback(topic, payload, **kwargs):
    logger.info(f"Received message from topic: {topic}")

    try:
        raw_payload = payload.decode("utf-8")
        logger.debug(f"Decoded payload: {raw_payload}")

        if "json" in topic:
            logger.info(f"Device Defender response: {raw_payload}")
            logger.debug("Processed as JSON message")
        else:
            cbor_data = cbor.loads(payload)
            logger.info(f"Device Defender response: {cbor_data}")
            logger.debug("Processed as CBOR message")
    except Exception as e:
        logger.error(f"Error processing message from topic {topic}: {e}")


def main():
    # Read in command-line parameters
    args = parse_args()

    # Configure Python logging
    log_level = logging.INFO
    if args.verbosity == "Debug":
        log_level = logging.DEBUG
    elif args.verbosity == "Warn":
        log_level = logging.WARNING
    elif args.verbosity == "Error":
        log_level = logging.ERROR

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler("device_defender_agent.log"),
        ],
    )

    logger.info("AWS IoT Device Defender Agent starting up")
    logger.info(f"Log level set to: {logging.getLevelName(log_level)}")

    # Initialize AWS CRT logging
    io.init_logging(getattr(io.LogLevel, args.verbosity), "stderr")
    if not args.dry_run:
        logger.info(
            "Running in live mode - will connect to AWS IoT and publish metrics"
        )

        client_id = ""
        thing_name = ""

        if not args.client_id:
            client_id = gethostname()
            logger.debug(f"Using hostname as client ID: {client_id}")
        else:
            client_id = args.client_id
            logger.debug(f"Using provided client ID: {client_id}")

        if not args.thing_name:
            thing_name = client_id
            logger.debug(f"Using client ID as thing name: {thing_name}")
        else:
            thing_name = args.thing_name
            logger.debug(f"Using provided thing name: {thing_name}")

        logger.info(f"Initializing IoT client for thing: {thing_name}")
        iot_client = IoTClientWrapper(
            args.endpoint,
            args.root_ca_path,
            args.certificate_path,
            args.private_key_path,
            client_id,
            args.signing_region,
            args.proxy_host,
            args.proxy_port,
            args.use_websocket,
        )

        logger.info("Connecting to AWS IoT...")
        iot_client.connect()

        # client_id must match a registered thing name in your account
        topic = "$aws/things/" + thing_name + "/defender/metrics/" + args.format
        logger.info(f"Device Defender topic: {topic}")

        # Subscribe to the accepted/rejected topics to indicate status of published metrics reports
        logger.info("Setting up Device Defender response subscriptions")
        iot_client.subscribe(topic + "/accepted", custom_callback)
        iot_client.subscribe(topic + "/rejected", custom_callback)
    else:
        logger.info("Running in dry-run mode - metrics will be printed to console only")

    sample_rate = args.upload_interval
    logger.info(f"Metrics collection interval: {sample_rate} seconds")
    logger.info(f"Metrics format: {args.format}")
    logger.info(f"Custom metrics enabled: {args.custom_metrics}")

    #  Collector samples metrics from the system, it can track the previous metric to generate deltas
    coll = collector.Collector(args.short_tags, args.custom_metrics)
    logger.info("Metrics collector initialized")

    metric = None
    first_sample = (
        True  # don't publish first sample, so we can accurately report delta metrics
    )
    iteration = 0

    logger.info("Starting metrics collection loop")

    try:
        while True:
            iteration += 1
            logger.debug(f"Metrics collection iteration: {iteration}")

            try:
                metric = coll.collect_metrics()
                logger.debug("Metrics collected successfully")

                if args.dry_run:
                    logger.info("Dry-run mode: metrics collected")
                    logger.info(
                        f"Metrics JSON:\n{metric.to_json_string(pretty_print=True)}"
                    )
                    if args.format == "cbor":
                        with open("cbor_metrics", "w+b") as outfile:
                            outfile.write(bytearray(metric.to_cbor()))
                        logger.debug("CBOR metrics written to file: cbor_metrics")
                else:
                    if first_sample:
                        logger.info(
                            "Skipping first sample to establish baseline for delta metrics"
                        )
                        first_sample = False
                    else:
                        logger.info(
                            f"Publishing metrics to Device Defender (iteration {iteration})"
                        )
                        if args.format == "cbor":
                            iot_client.publish(topic, bytearray(metric.to_cbor()))
                            logger.debug("Published CBOR metrics")
                        else:
                            iot_client.publish(topic, metric.to_json_string())
                            logger.debug("Published JSON metrics")

            except Exception as e:
                logger.error(f"Error in metrics collection iteration {iteration}: {e}")
                # Continue the loop despite errors

            logger.debug(f"Sleeping for {sample_rate} seconds")
            sleep(float(sample_rate))

    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down gracefully")

    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
        raise


if __name__ == "__main__":
    main()
