from setuptools import setup

setup(
    name="AWSIoTDeviceDefenderAgentSDK",
    version="2.0.0",
    description="AWS IoT Device Defender Agent SDK",
    url="https://github.com/aws-samples/aws-iot-device-defender-agent-sdk-python",
    author="Amazon Web Services",
    author_email="aws-iot-device-defender@amazon.com",
    license="APACHE.20",
    packages=["AWSIoTDeviceDefenderAgentSDK"],
    install_requires=["psutil", "cbor2", "awsiotsdk"],
    extras_require={"dev": ["flake8", "pytest"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    zip_safe=False,
)
