# Abrege

## Overview

This repository contains the necessary files to build and run the `abrege` service using Docker Compose. The service is configured to build its Docker image from a Dockerfile and supports various environment configurations through an `.env` file.

## Prerequisites

Before running the application, ensure that you have the following software installed on your system:
- Docker
- Docker Compose
- Makefile

## Setup

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Environment Configuration:**
   Create an `.env` file in the root directory of your project if it doesn't already exist. Populate it with the necessary environment variables. An example `.env` file might look like this:
   ```env
   BACKEND_PORT=8000
   TAG=latest
   ```

## Building and Running the Service

To build and run the `abrege` service, follow these steps:

1. **Build the Docker Image:**
   ```bash
   make build
   ```

2. **Run the Service:**
   ```bash
   make dev
   ```

3. **Stopping the Service:**
   To stop the service, run:
   ```bash
   make down
   ```

## Notes

- Ensure that the necessary environment variables are correctly set in the `.env` file to avoid build and runtime issues.
- Uncomment and configure the `deploy` section in the `docker-compose.yaml` file if resource constraints and GPU capabilities are needed.

## Troubleshooting

If you encounter any issues, check the following:
- Verify that Docker and Docker Compose are correctly installed and running.
- Ensure all environment variables in the `.env` file are set correctly.
- Check the Docker and Docker Compose documentation for more detailed troubleshooting steps.

## Contributing

If you wish to contribute to the project, please follow the standard procedures for forking the repository, making changes, and submitting a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Contact

For any inquiries or issues, please contact [your-email@example.com].

---

This README provides the necessary steps and configurations to get the `abrege` service up and running using Docker Compose. For any additional information or advanced configurations, refer to the Docker and Docker Compose documentation.
