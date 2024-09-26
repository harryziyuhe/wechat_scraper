
# WeChat Scraper

## Overview

WeChat Scraper is a Python package designed to automate the scraping of WeChat data. The package provides a streamlined process to set up a Windows Virtual Machine in VirtualBox, retrieve necessary parameters, and scrape WeChat data. This README will guide you through the installation, setup, and usage of the package.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [VirtualBox Setup](#virtualbox-setup)
  - [Automatic Setup](#automatic-setup)
  - [Manual Setup for Windows](#manual-setup-for-windows)
- [Running the Package](#running-the-package)
  - [Host Machine](#host-machine)
  - [VirtualBox](#virtualbox)
- [Usage](#usage)
- [License](#license)

## Features

- Automated setup of a Windows VM in VirtualBox.
- Automated parameter retrieval using `param_retriever.py`.
- Scraping of WeChat data through `wechat_scraper.py`.
- Support for running the scraping process in quiet mode.

## Installation

To install the package, clone the repository and use the following command:

\`\`\`bash
pip install .
\`\`\`

This will install the package and its dependencies on your host machine.

## VirtualBox Setup

### Automatic Setup

1. **Run the Setup Script on the Host Machine**:

   If you're using Linux or macOS, you can automate the setup of VirtualBox and the Windows VM by running the following command:

   \`\`\`bash
   setup-vm
   \`\`\`

   This command will:
   - Install VirtualBox on your host machine.
   - Download a Windows ISO file.
   - Create and configure a Windows VM.
   - Set up a shared folder between the host and the VM.

2. **Shared Folder**:

   By default, the shared folder is set to the repository directory. This allows easy access to scripts and data between the host and the VM.

### Manual Setup for Windows

If you are using a Windows host machine:

1. **Install VirtualBox**:

   Download and install VirtualBox from the [official website](https://www.virtualbox.org/wiki/Downloads).

2. **Download Windows ISO**:

   Download a Windows ISO from the [Microsoft website](https://www.microsoft.com/en-us/software-download/windows10).

3. **Set Up the VM**:

   Follow the instructions in the setup script (\`setup/setup_virtualbox_and_vm.sh\`) to manually create and configure the VM.

## Running the Package

### Host Machine

After installing the package, you can use the following command to set up the VirtualBox environment:

\`\`\`bash
setup-vm
\`\`\`

This will automate the VirtualBox setup and Windows VM configuration.

### VirtualBox

Once the Windows VM is set up and the shared folder is mounted (e.g., \`Z:\`), you can run the necessary scripts inside the VM.

1. **Navigate to the \`src/wechat_scraper/virtualbox\` Directory**:

   \`\`\`bash
   cd Z:\src\wechat_scraper\virtualbox
   \`\`\`

2. **Run \`param_retriever.py\`**:

   - **Normal Execution**:
     \`\`\`bash
     python param_retriever.py
     \`\`\`

   - **Quiet Mode**:
     \`\`\`bash
     python param_retriever.py --quiet
     \`\`\`
     or
     \`\`\`bash
     python param_retriever.py -q
     \`\`\`

3. **Run the WeChat Scraper on the Host Machine**:

   After retrieving parameters in VirtualBox, you can run the main scraper on the host machine:

   \`\`\`bash
   wechat-scraper --daymax=1000
   \`\`\`

   Add \`--verbose\` if you want more detailed output.

## Usage

### \`param_retriever.py\`

Retrieves the necessary parameters for scraping WeChat data.

- **Options**:
  - \`-q, --quiet\`: Run the script in quiet mode (suppress non-critical output).

### \`wechat_scraper.py\`

Main script for scraping WeChat data. Run this on the host machine after retrieving parameters from VirtualBox.

- **Options**:
  - \`--daymax\`: Maximum number of days to scrape (default is 2500).
  - \`-v, --verbose\`: Enable verbose mode.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
