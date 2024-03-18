# Topic Modeler Application

This application provides a graphical user interface (GUI) for topic modeling and analysis of textual data. It allows users to convert DOCX files to CSV, select files for analysis, specify the number of topics, visualize detailed information, hierarchy, and barchart representations of topics, and compare subsets of data for duplicate entries.

## Features

- DOCX to CSV conversion
- File selection for analysis
- Topic modeling with adjustable number of topics
- Detailed topic information display
- Hierarchy visualization of topics
- Barchart representation of topics
- Comparison of subsets for duplicate entries

## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.12 or later installed
- Conda (Anaconda or Miniconda) installed

## Setup

To set up the Topic Modeler application, follow these steps:

1. **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd <repository-folder>
    ```

2. **Create and activate a Conda environment:**

    Replace `<env_name>` with your desired environment name.

    ```bash
    conda create --name <env_name> python=3.12
    conda activate <env_name>
    ```

3. **Install required packages:**

    Ensure you are in the project root directory and run:

    ```bash
    conda install --file requirements.txt -c conda-forge
    ```

## Requirements

The application dependencies are listed in `requirements.txt`. This file includes all necessary Python packages, such as pandas, plotly, tkinter, and loguru.

## Running the Application

To run the Topic Modeler, execute the following command in the terminal:

```bash
python src/app.py
```

Ensure your working directory is the project's root folder. The GUI should launch, allowing you to interact with the application's features.

## Logging

Logs are saved to `app.log` with rotation set to one week. This can help with troubleshooting and tracking the application's operations over time.

## Contributing

Contributions to this project are welcome. Please ensure to follow the project's coding standards and submit pull requests for review.

## License

This project is licensed under the MIT License - see the `LICENSE.md` file for details.

## Acknowledgments

Thank you to all contributors who have helped with the development and improvement of this application.
