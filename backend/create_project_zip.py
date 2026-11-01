import os
import zipfile
from pathlib import Path

workspace_root = Path(__file__).resolve().parent.parent
output_zip = Path(r"C:\Users\bbipi\Desktop\KURINJI_Project.zip")

exclude_dirs = {'.venv', 'node_modules', '.git', '__pycache__', '.pytest_cache', 'dist', 'build', '.tempmediaStorage'}
exclude_exts = {'.pyc', '.pyo'}

print(f"Zipping {workspace_root} to {output_zip}...")
file_count = 0
total_size = 0

with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(workspace_root):
        # Skip excluded dirs
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext in exclude_exts:
                continue
            full_path = Path(root) / f
            rel_path = full_path.relative_to(workspace_root)
            zf.write(full_path, arcname=str(rel_path))
            file_count += 1
            total_size += full_path.stat().st_size

size_mb = output_zip.stat().st_size / (1024 * 1024)
print(f"Success! Zipped {file_count} files ({total_size / (1024*1024):.2f} MB uncompressed) into {output_zip} ({size_mb:.2f} MB)")
