import os
import tempfile

def save_uploaded_file(uploaded_file) -> str:
    """
    Save an uploaded file to a temporary location and return the path.
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    except Exception as e:
        print(f"Error saving file: {e}")
        return ""

def cleanup_temp_file(file_path: str):
    """
    Remove the temporary file.
    """
    if os.path.exists(file_path):
        os.remove(file_path)
