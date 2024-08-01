# Image Tagger with Tag Autocomplete

This project provides a GUI for viewing images, editing associated text files, and using tag autocomplete functionality.

## Features

- View images and edit associated text files
- Tag autocomplete using various tag sources
- Automatic download of missing tag files

## Requirements

- Python 3.7+
- Pillow (PIL)
- tkinter
- requests

## Installation

1. **Clone this repository:**
    ```bash
    git clone https://github.com/yourusername/your-repo-name.git
    cd your-repo-name
    ```

2. **(Optional) Create and activate a virtual environment:**

    Using `venv`:
    ```bash
    python -m venv env
    source env/bin/activate  # On Windows use `env\Scripts\activate`
    ```

    Using `conda`:
    ```bash
    conda create --name dataset-editor-env python=3.7
    conda activate dataset-editor-env
    ```

3. **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. **Run the script:**
    ```bash
    python edit-dataset.py
    ```

2. **On the first run, the script will automatically download necessary tag files.**

3. **Use the GUI to navigate through images, edit text, and use tag autocomplete.**

## Note

- The tag files are not included in this repository and will be downloaded automatically when needed. 
- Big thanks to DominikDoom (https://github.com/DominikDoom) the tags files are from [a1111-sd-webui-tagcomplete](https://github.com/DominikDoom/a1111-sd-webui-tagcomplete), which is licensed under the MIT License.
- If you want to use your own tag files, place them in a `tags` folder in the project directory.

## Project Structure

Your project should be organized as follows:

```plaintext
your-project-folder/
│
├── image_tagger.py  # Your main script
├── .gitignore
├── README.md
├── requirements.txt
└── tags/  # This folder will be created by the script when needed
```