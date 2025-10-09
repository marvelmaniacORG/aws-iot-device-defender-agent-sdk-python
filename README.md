# AWS IoT Device Defender Agent SDK (Python)

Example implementation of an AWS IoT Device Defender metrics collection agent,
and other Device Defender Python samples.

On starting up for the first time, the DD agent publishes the metric values read from the network stats to DD, without computing any metric values delta. It does this because when it starts up it does not have any information of the previously collected metric values. The side-effect of this is the device's metrics will indicate a large spike each time the device restarts or the agent is restarted which can cause false-positives. Now, we have updated the agent to not send any metrics if it cannot compute the delta.

The provided sample agent can be used as a basis to implement a custom metrics collection agent.

## Prerequisites

### Minimum System Requirements

The following requirements are shared with the [AWS IoT Device SDK for Python v2](https://github.com/aws/aws-iot-device-sdk-python-v2)

- Python 3.8+ for X.509 certificate-based mutual authentication via port 8883 and MQTT over WebSocket protocol with AWS Signature Version 4 authentication
- Python 3.8+ for X.509 certificate-based mutual authentication via port 443
- OpenSSL version 1.1.1+ (TLS version 1.2+) compiled with the Python executable for X.509 certificate-based mutual authentication

### Connect your Device to AWS IoT

If you have never connected your device to AWS IoT before, please follow the
[Getting Started with AWS IoT](https://docs.aws.amazon.com/iot/latest/developerguide/iot-gs.html)
Guide. Make sure you note the location of your certificates, you will
need to provide the location of these to the Device Defender Sample
Agent.

### Set up Device Defender Security Profile

**Important:** Device Defender requires a security profile to process and display metrics. Create a security profile that monitors the metrics emitted by this agent:

- `aws:num-listening-tcp-ports` - Number of listening TCP ports
- `aws:num-listening-udp-ports` - Number of listening UDP ports
- `aws:num-connections` - Number of established TCP connections
- `aws:all-bytes-in` - Bytes received over all network interfaces
- `aws:all-bytes-out` - Bytes sent over all network interfaces
- `aws:all-packets-in` - Packets received over all network interfaces
- `aws:all-packets-out` - Packets sent over all network interfaces

For detailed instructions on creating Device Defender behaviors and security profiles, see the [AWS IoT Device Defender Detect documentation](https://docs.aws.amazon.com/iot-device-defender/latest/devguide/detect-behaviors.html).

## Notes on the sample agent implementation

**client id**: The sample agent requires a client id that will also be used as the "Thing Name". This is only for the sake of making the sample easy to get started with. To customize this behavior, you can modify the way the agent generates the MQTT topic for publishing metrics reports, to use a value other than client id as the thing name portion of the topic.

**metric selection**: The sample agent attempts to gather all supported Device Defender metrics. Depending on your platform requirements and use case, you may wish to customize your agent to a subset of the metrics.

## Quickstart

### Installation

1. Clone the repository

```bash
git clone https://github.com/aws-samples/aws-iot-device-defender-agent-sdk-python.git
```

2. Install using pip

Pip is the easiest way to install the sample agent. It will take care of installing dependencies.

```bash
cd aws-iot-device-defender-agent-sdk-python
pip install .
```

Alternatively, you can install in development mode to make changes:

```bash
pip install -e .
```

### Running the Sample Agent

```bash
python agent.py --endpoint <your.custom.endpoint.amazonaws.com>  --rootCA </path/to/rootca>  --cert </path/to/cert> --key <path/to/key> --format json -i 300 -id <ThingName>
```

#### Command Line Options

To see a summary of all command-line options:

```bash
python agent.py --help
```

#### Test Metrics Collection Locally

```bash
python collector.py -n 1 -s 1
```

### Custom Metric Integration

The sample agent has a flag allowing it to publish custom metrics

```bash
python agent.py --include-custom-metrics --endpoint <your.custom.endpoint.amazonaws.com>  --rootCA </path/to/rootca>  --cert </path/to/cert> --key <path/to/key> --format json -i 300 -id <ThingName>
```

This flag will tell the agent to publish the custom metric `cpu_usage`, a `number` float representing the current CPU usage as a percent. How this looks in the generated report can be seen in the sample report below.

We can run the command seen below to create the `custom_metric` for `cpu_usage`.

```bash
aws iot create-custom-metric --metric-name "cpu_usage" --metric-type "number" --client-request-token "access-test" --region $AWS_REGION
```

After creating this `custom_metric` you will be able to create security profiles that use it.

```bash
# Step 1: Create the security profile
aws iot create-security-profile \
--security-profile-name CpuUsageIssue \
--security-profile-description "High-Cpu-Usage" \
--behaviors "[{\"name\":\"greater-than-75\",\"metric\":\"cpu_usage\",\"criteria\":{\"comparisonOperator\":\"greater-than\",\"value\":{\"number\":75},\"consecutiveDatapointsToAlarm\":5,\"consecutiveDatapointsToClear\":1}}]" \
--region $AWS_REGION

# Step 2: Attach the security profile to all registered things
aws iot attach-security-profile \
--security-profile-name CpuUsageIssue \
--security-profile-target-arn "arn:aws:iot:<your-region>:<your-account-id>:all/registered-things" \
--region $AWS_REGION
```

## AWS IoT Greengrass Integration

### Overview

AWS IoT Device Defender can be used in conjunction with AWS Greengrass.
Integration follows the standard Greengrass component deployment model,
making it easy to add AWS IoT Device Defender security to your
Greengrass Core devices.

### Prerequisites

1. [Greengrass environment setup](https://docs.aws.amazon.com/greengrass/v2/developerguide/getting-started-set-up-environment.html)
2. [Greengrass Core installed and running](https://docs.aws.amazon.com/greengrass/v2/developerguide/install-greengrass-v2.html)
3. Ensure you can successfully deploy and run a component on your core

### Using Device Defender with Greengrass Core devices

You can deploy a Device Defender to your Greengrass core in two ways:

1. Using the pre-built Greengrass Device Defender Component (_recommended_)
2. Create a custom component manually

#### Using Greengrass Component

The Device Defender Greengrass Component provides the most streamlined and automated means of deploying the Device Defender agent to your
Greengrass core, and is the recommended method of using Device Defender with Greengrass.

For detailed information about using Greengrass Components, see [Getting Started with Greengrass Components](https://docs.aws.amazon.com/greengrass/v2/developerguide/greengrass-components.html).
For information about configuring the Device Defender Component, see [Device Defender Component Details](https://docs.aws.amazon.com/greengrass/v2/developerguide/device-defender-component.html).

**Important: IoT Device Policy Requirements**

Before deploying the Device Defender component, ensure your Greengrass device certificate has an IoT policy that includes the necessary Greengrass permissions. The policy must include:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["iot:Connect", "iot:Publish", "iot:Subscribe", "iot:Receive"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "greengrass:ResolveComponentCandidates",
        "greengrass:GetComponentVersionArtifact"
      ],
      "Resource": "*"
    }
  ]
}
```

**Console Deployment Steps:**

1. **Navigate to AWS IoT Console**

   - Go to the [AWS IoT Console](https://console.aws.amazon.com/iot)
   - In the left navigation pane, expand **Greengrass devices**
   - Click **Core devices**

2. **Select Your Greengrass Core Device**

   - Find and click on your Greengrass core device
   - This will open the device details page

3. **Create a New Deployment**

   - Click the **Deploy to device** button
   - This will start the deployment creation wizard

4. **Configure Deployment Target**

   - **Deployment target**: Your core device should already be selected
   - **Deployment name**: Enter a descriptive name (e.g., `DeviceDefenderDeployment`)
   - Click **Next**

5. **Select Components**

   - In the **Public components** tab, search for "Device Defender"
   - Select **aws.iot.DeviceDefender** from the list
   - Click **Next**

6. **Configure Components**

   - **Component version**: Select the latest version (or leave as default)
   - **Configuration**: You can use the default configuration or customize:
     ```json
     {
       "SampleIntervalSeconds": "300",
       "DeviceDefenderThingName": "{iot:thingName}",
       "ReportFormat": "JSON"
     }
     ```
   - Click **Next**

7. **Configure Advanced Settings** (Optional)

   - **Component dependencies**: Leave as default
   - **Deployment policies**: Configure as needed for your environment
   - Click **Next**

8. **Review and Deploy**

   - Review your deployment configuration
   - Click **Deploy**

9. **Monitor Deployment Status**

   - The deployment will show as "In progress"
   - Wait for the status to change to "Succeeded"
   - You can monitor progress in the **Deployments** tab of your core device

10. **Verify Device Defender is Running**
    - Check the **Components** tab on your core device
    - You should see `aws.iot.DeviceDefender` listed as "Running"
    - Check CloudWatch Logs for Device Defender metrics being published

#### Create Your Custom Component Manually

This approach creates a Lambda function and imports it as a Greengrass component. Follow the [AWS documentation for importing Lambda functions as components](https://docs.aws.amazon.com/greengrass/v2/developerguide/import-lambda-function-cli.html).

**Note:** Due to platform-specific binary extensions in the psutil package, perform these steps on the same platform where you plan to deploy.

### Step 1: Clone Repository and Set Up Environment

1. **Set AWS region environment variable:**

```bash
export AWS_REGION=us-east-1
```

**Note:** Replace `us-east-1` with your actual AWS region.

2. **Clone the repository:**

```bash
git clone https://github.com/aws-samples/aws-iot-device-defender-agent-sdk-python.git
cd aws-iot-device-defender-agent-sdk-python
```

3. **Create and activate virtual environment:**

```bash
python3 -m venv metrics_lambda_environment
source metrics_lambda_environment/bin/activate
```

4. **Install the Device Defender SDK and dependencies:**

```bash
pip install .
```

### Step 2: Create Lambda Package

4. **Create Lambda directory:**

```bash
mkdir metrics_lambda
cd metrics_lambda
```

5. **Copy the Greengrass agent script:**

```bash
cp ../samples/greengrass/greengrass_core_metrics_agent/greengrass_defender_agent.py .
```

6. **Copy the Device Defender SDK:**

```bash
cp -R ../AWSIoTDeviceDefenderAgentSDK .
```

7. **Copy Python dependencies:**

```bash
cp -R ../metrics_lambda_environment/lib/python*/site-packages/psutil .
cp -R ../metrics_lambda_environment/lib/python*/site-packages/cbor2 .
cp -R ../metrics_lambda_environment/lib/python*/site-packages/awscrt .
cp -R ../metrics_lambda_environment/lib/python*/site-packages/awsiot .
```

8. **Create deployment package:**

```bash
zip -r function.zip *
```

### Step 3: Create Lambda Function in AWS

9. **Create a new Lambda function:**

Create the Lambda function using the AWS CLI with the deployment package from Step 2:

```bash
aws lambda create-function \
--function-name DeviceDefenderLambda \
--zip-file fileb://greengrass_defender_metrics_lambda.zip \
--role arn:aws:iam::<your-account-id>:role/<your-lambda-execution-role> \
--runtime python3.13 \
--handler greengrass_defender_agent.function_handler \
--timeout 900 \
--memory-size 128 \
--region $AWS_REGION
```

**Note:** Replace `<your-account-id>` and `<your-lambda-execution-role>` with your actual AWS account ID and Lambda execution role name.

10. **Publish a new version:**

After creating the function, **publish a new version**. This is required for Greengrass component import:

```bash
aws lambda publish-version --function-name DeviceDefenderLambda --region $AWS_REGION
```

**Important:** Make note of the Lambda function ARN **with version number** after publishing, as you will need it in Step 4 to configure the Greengrass component. The ARN will be in the format:

```
arn:aws:lambda:<region>:<account-id>:function:<function-name>:<version>
```

Example: `arn:aws:lambda:$AWS_REGION:123456789012:function:DeviceDefender:1`

### Step 4: Import as Greengrass Component

12. **Create component configuration file (`lambda-function-component.json`):**

**Note:** A sample configuration file is provided in the `/samples/greengrass/greengrass_core_metrics_agent/` directory that you can use as a template.

```json
{
  "lambdaFunction": {
    "lambdaArn": "arn:aws:lambda:<region>:<your-account-id>:function:DeviceDefenderLambda:<version>",
    "componentName": "com.example.DeviceDefenderLambda",
    "componentVersion": "1.0.0",
    "componentPlatforms": [
      {
        "name": "linux",
        "attributes": {
          "os": "linux"
        }
      }
    ],
    "componentLambdaParameters": {
      "maxInstancesCount": 1,
      "pinned": true,
      "timeoutInSeconds": 900,
      "environmentVariables": {
        "SAMPLE_INTERVAL_SECONDS": "300",
        "PROCFS_PATH": "/proc"
      },
      "linuxProcessParams": {
        "isolationMode": "NoContainer"
      }
    }
  }
}
```

13. **Import Lambda as Greengrass component:**

```bash
aws greengrassv2 create-component-version \
--cli-input-json file://lambda-function-component.json \
--region $AWS_REGION
```

### Step 5: Deploy Component with IPC Permissions

14. **Deploy to your Greengrass device with proper IPC permissions:**

The component requires specific IPC permissions to publish metrics to AWS IoT Core. Deploy using the following command which includes the necessary access control policy:

```bash
aws greengrassv2 create-deployment \
--target-arn "arn:aws:iot:$AWS_REGION:<your-account-id>:thing/<your-thing-name>" \
--deployment-name "Device Defender Deployment" \
--components '{
  "com.example.DeviceDefenderLambda": {
    "componentVersion": "1.0.0",
    "configurationUpdate": {
      "merge": "{\"accessControl\":{\"aws.greengrass.ipc.mqttproxy\":{\"com.example.DeviceDefenderLambda:mqttproxy:1\":{\"policyDescription\":\"Allows access to publish to Device Defender topic\",\"operations\":[\"aws.greengrass#PublishToIoTCore\"],\"resources\":[\"$aws/things/*/defender/metrics/json\"]}}}}"
    }
  }
}' \
--region $AWS_REGION
```

**Important:** Replace `<your-account-id>` and `<your-thing-name>` with your actual AWS account ID and Greengrass thing name.

The component will now run as a containerized Lambda function on your Greengrass device, collecting Device Defender metrics with access to system resources through the mounted `/proc` filesystem.

### Step 6: Verify Deployment

15. **Check Device Defender Console:**

- Navigate to **AWS IoT Console** → **Defend** → **Device Defender** → **Detect**
- Your device should appear in the devices list with recent metrics data

16. **Check Greengrass Component Logs - (Optional)**

Run the following comand to view the logs for this component on the Greengrass device.

```bash
sudo tail /greengrass/v2/logs/com.example.DeviceDefenderLambda.log
```

#### Troubleshooting

##### Common Issues and Solutions

**1. IPC Permission Errors**

If you see errors like `✗ Failed to publish metrics #X: .` in the logs, this indicates missing IPC permissions. Ensure you deployed with the access control policy as shown in Step 5.

**2. Component Not Starting**

Check the Greengrass core logs:

```bash
sudo tail -f /greengrass/v2/logs/greengrass.log
```

**3. Lambda Function Import Errors**

Ensure your Lambda function ARN in `lambda-function-component.json` is correct and includes the version number.

**4. Missing Dependencies**

If you see import errors, ensure all dependencies (psutil, cbor2, AWSIoTDeviceDefenderAgentSDK) are included in your Lambda package.

##### Reviewing AWS IoT Device Defender device metrics using AWS IoT Console

1. Temporarily modify your publish topic in your Greengrass lambda to
   something such as metrics/test
2. Deploy the lambda
3. Add a subscription to the temporary topic in the "Test" section of
   the IoT console. Shortly, you should see the metrics your Greengrass Core
   is emitting

##### Debugging Steps

1. **Check component status:**

```bash
sudo /greengrass/v2/bin/greengrass-cli component list
```

2. **View component logs:**

```bash
sudo tail -f /greengrass/v2/logs/com.example.DeviceDefenderLambda.log
```

3. **Restart Greengrass core if needed:**

```bash
sudo systemctl restart greengrass
```

## Metrics Report Details

### Overall Structure

| Long Name      | Short Name | Required | Type   | Constraints | Notes                                          |
| -------------- | ---------- | -------- | ------ | ----------- | ---------------------------------------------- |
| header         | hed        | Y        | Object |             | Complete block required for well-formed report |
| metrics        | met        | Y        | Object |             | Complete block required for well-formed report |
| custom_metrics | cmet       | N        | Object |             | Complete block required for well-formed report |

#### Header Block

| Long Name | Short Name | Required | Type    | Constraints | Notes                                                                        |
| --------- | ---------- | -------- | ------- | ----------- | ---------------------------------------------------------------------------- |
| report_id | rid        | Y        | Integer |             | Monotonically increasing value, epoch timestamp recommended                  |
| version   | v          | Y        | String  | Major.Minor | Minor increments with addition of field, major increments if metrics removed |

#### Metrics Block

##### TCP Connections

| Long Name               | Short Name | Parent Element          | Required | Type   | Constraints | Notes                          |
| ----------------------- | ---------- | ----------------------- | -------- | ------ | ----------- | ------------------------------ |
| tcp_connections         | tc         | metrics                 | N        | Object |             |                                |
| established_connections | ec         | tcp_connections         | N        | List   |             | ESTABLISHED TCP State          |
| connections             | cs         | established_connections | N        | List   |             |                                |
| remote_addr             | rad        | connections             | Y        | Number | ip:port     | ip can be ipv6 or ipv4         |
| local_port              | lp         | connections             | N        | Number | >0          |                                |
| local_interface         | li         | connections             | N        | String |             | interface name                 |
| total                   | t          | established_connections | N        | Number | >= 0        | Number established connections |

##### Listening TCP Ports

| Long Name           | Short Name | Parent Element      | Required | Type   | Constraints | Notes                       |
| ------------------- | ---------- | ------------------- | -------- | ------ | ----------- | --------------------------- |
| listening_tcp_ports | tp         | metrics             | N        | Object |             |                             |
| ports               | pts        | listening_tcp_ports | N        | List   | > 0         |                             |
| port                | pt         | ports               | N        | Number | >= 0        | ports should be numbers > 0 |
| interface           | if         | ports               | N        | String |             | Interface Name              |
| total               | t          | listening_tcp_ports | N        | Number | >= 0        |                             |

##### Listening UDP Ports

| Long Name           | Short Name | Parent Element      | Required | Type   | Constraints | Notes                       |
| ------------------- | ---------- | ------------------- | -------- | ------ | ----------- | --------------------------- |
| listening_udp_ports | up         | metrics             | N        | Object |             |                             |
| ports               | pts        | listening_udp_ports | N        | List   | > 0         |                             |
| port                | pt         | ports               | N        | Number | > 0         | ports should be numbers > 0 |
| interface           | if         | ports               | N        | String |             | Interface Name              |
| total               | t          | listening_udp_ports | N        | Number | >= 0        |                             |

##### Network Stats

| Long Name     | Short Name | Parent Element | Required | Type   | Constraints        | Notes |
| ------------- | ---------- | -------------- | -------- | ------ | ------------------ | ----- |
| network_stats | ns         | metrics        | N        | Object |                    |       |
| bytes_in      | bi         | network_stats  | N        | Number | Delta Metric, >= 0 |       |
| bytes_out     | bo         | network_stats  | N        | Number | Delta Metric, >= 0 |       |
| packets_in    | pi         | network_stats  | N        | Number | Delta Metric, >= 0 |       |
| packets_out   | po         | network_stats  | N        | Number | Delta Metric, >= 0 |       |

##### Custom Metrics

| Long Name | Short Name | Parent Element | Required | Type   | Constraints | Notes |
| --------- | ---------- | -------------- | -------- | ------ | ----------- | ----- |
| cpu_usage | cpu        | custom_metrics | N        | Number |             |       |

### Sample Metrics Reports

#### Long Field Names

```javascript
{
    "header": {
        "report_id": 1529963534,
        "version": "1.0"
    },
    "metrics": {
        "listening_tcp_ports": {
            "ports": [
                {
                    "interface": "eth0",
                    "port": 24800
                },
                {
                    "interface": "eth0",
                    "port": 22
                },
                {
                    "interface": "eth0",
                    "port": 53
                }
            ],
            "total": 3
        },
        "listening_udp_ports": {
            "ports": [
                {
                    "interface": "eth0",
                    "port": 5353
                },
                {
                    "interface": "eth0",
                    "port": 67
                }
            ],
            "total": 2
        },
        "network_stats": {
            "bytes_in": 1157864729406,
            "bytes_out": 1170821865,
            "packets_in": 693092175031,
            "packets_out": 738917180
        },
        "tcp_connections": {
            "established_connections":{
                "connections": [
                    {
                    "local_interface": "eth0",
                    "local_port": 80,
                    "remote_addr": "192.168.0.1:8000"
                    },
                    {
                    "local_interface": "eth0",
                    "local_port": 80,
                    "remote_addr": "192.168.0.1:8000"
                    }
                ],
                "total": 2
            }
        }
    },
    "custom_metrics": {
        "cpu_usage": [
            {
                "number": 26.1
            }
        ]
    }
}
```

#### Short Field Names

```javascript
{
    "hed": {
        "rid": 1529963534,
        "v": "1.0"
    },
    "met": {
        "tp": {
            "pts": [
                {
                    "if": "eth0",
                    "pt": 24800
                },
                {
                    "if": "eth0",
                    "pt": 22
                },
                {
                    "if": "eth0",
                    "pt": 53
                }
            ],
            "t": 3
        },
        "up": {
            "pts": [
                {
                    "if": "eth0",
                    "pt": 5353
                },
                {
                    "if": "eth0",
                    "pt": 67
                }
            ],
            "t": 2
        },
        "ns": {
            "bi": 1157864729406,
            "bo": 1170821865,
            "pi": 693092175031,
            "po": 738917180
        },
        "tc": {
            "ec":{
                "cs": [
                    {
                    "li": "eth0",
                    "lp": 80,
                    "rad": "192.168.0.1:8000"
                    },
                    {
                    "li": "eth0",
                    "lp": 80,
                    "rad": "192.168.0.1:8000"
                    }
                ],
                "t": 2
            }
        }
    },
    "cmet": {
        "cpu": [
            {
                "number": 26.1
            }
        ]
    }
}
```

## API Documentation

You can find the API documentation [here](https://aws-iot-device-defender-agent-sdk.readthedocs.io/en/latest/)

## Resources

- [AWS IoT Device Defender Documentation](https://docs.aws.amazon.com/iot/latest/developerguide/device-defender.html)
- [AWS IoT Device SDK for Python](https://github.com/aws/aws-iot-device-sdk-python)
- [AWS IoT Greengrass Documentation](https://docs.aws.amazon.com/greengrass/latest/developerguide/)
