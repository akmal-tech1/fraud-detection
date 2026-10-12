import zipfile
import os

project_root = r"C:\Users\akmal\OneDrive\Documents\Default Project"
zip_path = r"..\Financial-Fraud-Detection.zip"

exclude_dirs = {".git", "venv", "node_modules"}

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(project_root):
        # Filter out excluded directories from descent
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        
        for file in files:
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, project_root)
            
            skip = False
            
            # Check each path component against excluded dirs
            parts = relpath.replace("\\", "/").split("/")
            for part in parts:
                if part in exclude_dirs:
                    skip = True
                    break
            
            # Check file extensions
            if any(file.endswith(ext) for ext in [".db", ".joblib"]):
                skip = True
            
            # Check for .env file specifically
            if file == ".env" or relpath.startswith(".env/"):
                skip = True
            
            if not skip and os.path.isfile(filepath):
                zf.write(filepath, relpath)

print("Zip created successfully")

# Verify
with zipfile.ZipFile(zip_path) as z:
    count = len(z.namelist())
    names = z.namelist()
    print(f"Files in zip: {count}")
    print(f"Contains .git: {any('.git' in n for n in names)}")
    print(f"Contains venv: {any('venv' in n for n in names)}")
    print(f"Contains node_modules: {any('node_modules' in n for n in names)}")
    print(f"Contains .env: {any('.env' in n for n in names)}")
    print(f"Contains fraud_detection.db: {any('fraud_detection.db' in n for n in names)}")
    print(f"Contains .joblib: {any('.joblib' in n for n in names)}")