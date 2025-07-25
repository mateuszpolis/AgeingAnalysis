# DA_batch_client

**Note**: The `DA_batch_client.py` file contains proprietary code and is not included in this repository for legal reasons. The application is designed to handle the missing file gracefully by returning empty DataFrames when the module is not available.

This project is a client instance of the DA_batch_client application for the DCS.

## Getting started

DA_batch_client is an application based on DARMA. Its main aim is to easily download the big data files from the database and also to simplify downloading of recurring requests.

## Description

DA_batch_client is an application written in Python, for the description of the used libraries please refer to the **Installation**.

Users specify the input file with the exact structure as shown in **input.csv** example. The DA_batch_client reads the file and sends requests to the server.

The name of **output file**  is also specified by users. DA_batch_client creates separate files for aliases and element_names. If the input file contains more than 200 datapoints, output file is divided to multiple chunks, each of which contains maximum of 200 datapoints.

Chunks specification can be found in the file **datapoints_list.txt** saved automatically by the DA_batch_client. This file is rewritten by each run of the application, in case user wants to backup the file, it has to be copied to the different directory.

## Installation

DA_batch_client runs on a Python 3.12.6. For the Python installation, please check: [Python documentation](https://www.python.org/downloads/release/python-3126/).

Additionally, these libraries needs to be installed:
- requests
- base64

## Usage

To run DA_batch_client, use this command:

```
python DA_batch_client.py input_file_name.csv output_file_name.csv
```
Input file name and output file name depends on user's preferences, the order of the names must be maintained when running the application.

### Input file structure

The structure of the input file needs to be maintained the same as in the example in this repository. It is a **.csv** file, the first collumn represents the keyword for processing.

The keywords are:
- timefrom
- timeto
- schema
- element
- alias

All datapoints can be listed in one row:
```
elements temperature1;temperature2;temperature3;
```
or as follows:
```
element; temperature1
element; temperature2
element; temperature3
```

The same rule applies to aliases, but be careful to **always** separate the alias and element type of the datapoint:
```
element; temperature_element1
alias; temperature_alias1
```

### Output file structure

Results retrieved from the databased are stored in the output file. The structure is similiar to the output files from DARMA:

```
date;time;element_name/alias;value
```
