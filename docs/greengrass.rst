AWS IoT Greengrass Integration
==============================

The AWS IoT Device Defender Agent SDK can be deployed as a Lambda component on AWS IoT Greengrass devices for continuous edge monitoring.

Overview
--------

AWS IoT Greengrass integration allows you to:

* Deploy Device Defender as a long-running Lambda component
* Collect metrics continuously on edge devices
* Publish metrics to AWS IoT Core via Greengrass IPC
* Maintain device security monitoring even when offline

Architecture
------------

The Greengrass deployment uses:

* **Lambda Function**: Contains the Device Defender agent code
* **IPC Communication**: Secure communication with Greengrass core
* **Component Configuration**: Defines runtime parameters and permissions
* **Access Control Policies**: Grant IPC permissions for IoT Core publishing

Quick Start
-----------

1. **Set up environment**::

    export AWS_REGION=us-east-1

2. **Create Lambda function** with the Device Defender code

3. **Import as Greengrass component** using the provided configuration

4. **Deploy with IPC permissions** for IoT Core publishing

Component Configuration
-----------------------

The Greengrass component requires:

* **Pinned execution**: ``"pinned": true`` for continuous operation
* **Timeout**: 900 seconds (15 minutes) maximum
* **Environment variables**: ``SAMPLE_INTERVAL_SECONDS``, ``PROCFS_PATH``
* **IPC permissions**: ``aws.greengrass#PublishToIoTCore`` operation

Example component configuration::

    {
      "lambdaFunction": {
        "lambdaArn": "arn:aws:lambda:$AWS_REGION:<account-id>:function:DeviceDefender:<version>",
        "componentName": "com.example.DeviceDefenderLambda",
        "componentVersion": "1.0.54",
        "componentLambdaParameters": {
          "maxInstancesCount": 1,
          "pinned": true,
          "timeoutInSeconds": 900,
          "environmentVariables": {
            "SAMPLE_INTERVAL_SECONDS": "300",
            "PROCFS_PATH": "/proc"
          }
        }
      }
    }

Deployment with IPC Permissions
-------------------------------

Deploy the component with proper access control::

    aws greengrassv2 create-deployment \
    --target-arn "arn:aws:iot:$AWS_REGION:<account-id>:thing/<thing-name>" \
    --deployment-name "Device Defender Deployment" \
    --components '{
      "com.example.DeviceDefenderLambda": {
        "componentVersion": "1.0.54",
        "configurationUpdate": {
          "merge": "{\"accessControl\":{\"aws.greengrass.ipc.mqttproxy\":{\"com.example.DeviceDefenderLambda:mqttproxy:1\":{\"policyDescription\":\"Allows access to publish to Device Defender topic\",\"operations\":[\"aws.greengrass#PublishToIoTCore\"],\"resources\":[\"$aws/things/*/defender/metrics/json\"]}}}}"
        }
      }
    }' \
    --region $AWS_REGION

Monitoring and Troubleshooting
-------------------------------

**Check component logs**::

    sudo tail -f /greengrass/v2/logs/com.example.DeviceDefenderLambda.log

**Common issues**:

* **Lambda timeout**: Increase timeout to 900 seconds
* **IPC permission errors**: Verify access control policies in deployment
* **Metrics collection errors**: Check ``/proc`` filesystem access
* **Component restart**: Use ``sudo systemctl restart greengrass``

**Successful operation indicators**:

* ``✓ Connected to Greengrass IPC``
* ``✓ Published metrics #X to $aws/things/<device>/defender/metrics/json via Greengrass IPC``
* Metrics visible in AWS IoT MQTT Test Client
* Device appears in Device Defender console

For complete setup instructions, see the main repository README.