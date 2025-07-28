"""This module contains functions for interacting with the DARMA API server."""

import base64
import json
import os
import sys
import time

import requests


def upload_file(file_path, flask_url):
    """Send a file to the Flask app and retrieve one or more client IDs.

    Args:
        file_path (str): Path to the file to upload.
        flask_url (str): URL of the Flask app's upload endpoint.

    Returns:
        List[str]: A list of client IDs if successful, otherwise None.
    """
    try:
        # Read and encode the file in Base64
        with open(file_path, "rb") as file:
            file_content = base64.b64encode(file.read()).decode("utf-8")

        # Prepare JSON payload
        payload = {
            "filename": file_path.split("/")[-1],  # Extract filename from path
            "file_content": file_content,
        }

        # Send the request
        response = requests.post(
            flask_url, json=payload, timeout=600
        )  # 10 minutes for large file uploads

        # Check response
        if response.status_code == 200:
            data = response.json()
            client_ids = data.get("client_ids", [data.get("client_id")])
            print("Upload successful.")
            return client_ids
        else:
            print("Failed to upload file:", response.text)
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def get_result_file(client_id, flask_url):
    """Request the result file from the Flask app using the client ID.

    Args:
        client_id (str): The client ID received after file upload.
        flask_url (str): URL of the Flask app's result endpoint.

    Returns:
        str: The result file content in Base64 if successful, otherwise None.
    """
    try:
        # Prepare JSON payload
        payload = {"client_id": client_id}

        # Send the request
        response = requests.post(
            flask_url, json=payload, timeout=600
        )  # 10 minutes for large data transfers

        # Check response
        if response.status_code == 200:
            data = response.json()
            print(f"Result file received successfully for client ID {client_id}.")
            return data["result_file"]
        else:
            print(
                f"Failed to retrieve result file for client ID {client_id}:",
                response.text,
            )
            return None
    except Exception as e:
        print(f"An error occurred for client ID {client_id}: {e}")
        return None


def append_result_file(base64_content, output_path):
    """Decode the Base64-encoded result file content and append it to the output file.

    Ensures the header is added only once.
    If the output file does not exist, it is created.

    Args:
        base64_content (str): The Base64-encoded content of the result file.
        output_path (str): Path to the output file.
    """
    try:
        # Decode Base64 content
        file_content = base64.b64decode(base64_content).decode("utf-8")

        # Separate the header and the content
        lines = file_content.splitlines()
        header = lines[0]  # First line is the header
        data = "\n".join(lines[1:])  # Remaining lines are the data

        # Check if the output file already exists and contains a header
        header_exists = False
        if os.path.exists(output_path):
            with open(output_path) as file:
                first_line = file.readline().strip()
                header_exists = first_line == header

        # Open the file in append mode
        with open(output_path, "a") as file:
            if not header_exists:
                # Write the header if it does not already exist
                file.write(header + "\n")
            # Append the data
            file.write(data + "\n")

        print(f"Appended result content to {output_path}")
    except Exception as e:
        print(f"Failed to append result file: {e}")


def save_result_file(base64_content, output_path):
    """Save the Base64-encoded result file content to a local file.

    Args:
        base64_content (str): The Base64-encoded content of the result file.
        output_path (str): Path to save the output file.
    """
    try:
        # Decode Base64 content
        file_content = base64.b64decode(base64_content)

        # Write to a file
        with open(output_path, "wb") as file:
            file.write(file_content)
        print(f"Result file saved to {output_path}")
    except Exception as e:
        print(f"Failed to save result file: {e}")


def request_and_save_parsed_data(client_ids, parsed_data_url, output_path):
    """Request data from the server for the given client IDs and save it to a file.

    Args:
        client_ids (List[str]): A list of client IDs for which parsed data is requested.
        parsed_data_url (str): URL of the Flask app's parsed data endpoint.
        output_path (str): Path to save the output parsed data file.
    """
    try:
        # Prepare JSON payload
        payload = {"client_ids": client_ids}

        # Send the request
        response = requests.post(
            parsed_data_url, json=payload, timeout=600
        )  # 10 minutes for large data transfers

        # Check response
        if response.status_code == 200:
            data = response.json()

            if "data" in data:
                # Sort chunks by their numerical order (chunk_1, chunk_2, etc.)
                sorted_chunks = sorted(
                    data["data"].items(),
                    key=lambda x: int(
                        x[0].split("_")[-1]
                    ),  # Extract the number after the last underscore
                )

                # Save parsed data to a file with proper formatting
                with open(output_path, "w") as file:
                    for chunk_name, chunk_data in sorted_chunks:
                        file.write(f"{chunk_name}:\n")
                        file.write(json.dumps(chunk_data, indent=4))
                        file.write("\n\n")  # Add spacing between chunks for readability
                print(f"Parsed data saved to {output_path}")
            else:
                print("Response data does not contain 'data' key:", response.text)
        else:
            print("Failed to retrieve parsed data:", response.text)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <input_file_path> <output_file_path>")
        sys.exit(1)

    # Define file paths and Flask URLs
    input_file_path = sys.argv[1]
    output_file_path = sys.argv[2]
    upload_url = "http://agrana-dev.cern.ch:5050/upload_base64"
    result_url = "http://agrana-dev.cern.ch:5050/generate_result"
    parsed_data_url = "http://agrana-dev.cern.ch:5050/get_parsed_data"
    parsed_data_file_path = "datapoints_list.txt"

    # Measure time
    start_time = time.time()  # Start timer

    # Step 1: Upload file and get client IDs
    client_ids = upload_file(input_file_path, upload_url)

    if client_ids:
        if len(client_ids) > 1:
            request_and_save_parsed_data(
                client_ids, parsed_data_url, parsed_data_file_path
            )
        # Handle both single and multiple client IDs
        for idx, client_id in enumerate(client_ids, start=1):
            # Step 2: Request the result file using the client ID
            result_file_base64 = get_result_file(client_id, result_url)

            if result_file_base64:
                # Step 3: Save the result file locally
                output_path = (
                    f"{output_file_path.rsplit('.', 1)[0]}_{idx}."
                    f"{output_file_path.rsplit('.', 1)[-1]}"
                    if len(client_ids) > 1
                    else output_file_path
                )
                save_result_file(result_file_base64, output_path)

    # Measure the total elapsed time
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time:.2f} seconds")
