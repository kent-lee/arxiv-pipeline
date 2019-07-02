# arXiv Pipeline

This is a simple project created to demonstrate the workflow of a data pipeline. The source data is from the [RSS](http://export.arxiv.org/rss/cs) feed of the [Computer Science arXiv](https://arxiv.org/list/cs/new). The workflow is as follow:

![alt text](doc/workflow.png?raw=true "workflow")

## Instructions

1. install [Python 3.6+](https://www.python.org/)

2. install `pip3` 

    ```bash
    sudo apt install python3-pip
    ```

3. install required modules

    ```bash
    pip3 install -r requirements.txt
    ```

4. setup a home for `airflow` module

    ```bash
    export AIRFLOW_HOME=~/airflow
    ```

5. start the webserver

    ```bash
    airflow webserver
    ```

6. visit `localhost:8080` in the browser and set the `arxiv-pipeline` DAG to `On` in the webserver UI

7. open another terminal and start the schedular

    ```bash
    airflow schedular
    ```

## Note

- this program is only tested on Unbuntu 18.04
- my AWS credentials are not in the source code
