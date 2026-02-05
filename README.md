# Streamlit PDF Merger 📄

**Tired of merging PDFs on weird, full of ads websites? Well, me too**, so I have created an app that won't store your data.
Drag-and-drop PDF merging tool built with **Streamlit**. This app allows you to upload multiple PDFs, reorder them, select specific page ranges, and merge them into a single document.

## Features

* **Drag & drop interface:** Upload by dropping the files into the app, or browse them locally
* **Flexible reordering:** Reorder merging sequence by dragging the files in the UI
* **Page range selection:** Merge entire files or extract specific pages (e.g., `1-3, 5, 8-10`)
* **Real-time metadata:** View page counts and file sizes before merging

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/JPacoch/pdfmerge.git
cd pdf-merger
```

### 2. Create a virtual environment
``` bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
You will need streamlit and pypdf
```bash
pip install -r reqs.txt
```

## Usage

### 1. Run the app:
```bash
streamlit run app.py
```

### 2. Upload PDFs: drag your files into the upload area

### 3. Order files
Use the arrow buttons (or drag items if the optional package is installed) to set the merge order

### 4. Select pages
    - Switch "Merge mode" in the sidebar to `Select page ranges`
    - Enter ranges like `3-5` or specific pages like `1,3,5` for each file

### 5. Merge & download

## License 

This project is open-source and available under the MIT License.
