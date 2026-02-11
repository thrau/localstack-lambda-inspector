LocalStack Lambda Inspector
===============================

An extension to inspect lambda invocations in localstack.
It provides a streamlit powered UI that lets you explore the input, output, and logs of each lambda invocation that occured in localstack.

> [!WARNING]
> This extension is experimental and primarily a proof of concept. Use at your own risk.

<img width="2560" height="1573" alt="image" src="https://github.com/user-attachments/assets/49a709f5-5c85-49c7-8ff4-fc45c87b58e4" />

## Install from GitHub repository

You can install the extension directly from GitHub.

```bash
localstack extensions install "git+https://github.com/thrau/localstack-lambda-inspector/#egg=localstack-lambda-inspector"
```

## Install local development version

To install the extension into localstack in developer mode, you will need Python >=3.10, and create a virtual environment in the extensions project.

In the newly generated project, simply run

```bash
make install
```

Then, to enable the extension for LocalStack, run

```bash
localstack extensions dev enable .
```

You can then start LocalStack with `EXTENSION_DEV_MODE=1` to load all enabled extensions:

```bash
EXTENSION_DEV_MODE=1 localstack start
```
