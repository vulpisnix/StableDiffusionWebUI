import os
import requests
from huggingface_hub import HfApi, hf_hub_url

class PipelineDownloader:
    def __init__(self, repo_id: str, local_dir: str = "./sd_model_cache", branch: str = "main"):
        self.repo_id = repo_id
        self.local_dir = os.path.join(local_dir, "models--"+repo_id.replace("/", "--"))
        self.branch = branch
        os.makedirs(local_dir, exist_ok=True)
        self.api = HfApi()

    def list_files(self):
        """Alle Dateien der Pipeline auf Hugging Face listen"""
        files = self.api.list_repo_files(self.repo_id, revision=self.branch)
        return files

    def download_file(self, filename, callback=None):
        """Eine einzelne Datei mit Fortschritt herunterladen"""
        url = hf_hub_url(self.repo_id, filename, revision=self.branch)
        local_path = os.path.join(self.local_dir, filename)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # HEAD request für Dateigröße
        head = requests.head(url, allow_redirects=True)
        total = int(head.headers.get("Content-Length", 0))

        # Stream Download
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            downloaded = 0
            with open(local_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if callback and total > 0:
                            percent = int(downloaded / total * 100)
                            callback(filename, percent)

        return local_path

    def download_all(self, callback_file=None, callback_global=None):
        """Alle Dateien herunterladen, mit Callback pro Datei & Gesamt"""
        files = self.list_files()
        total_files = len(files)
        downloaded_files = 0

        for filename in files:
            # Pro-Datei Callback
            def file_cb(fname, percent):
                if callback_file:
                    callback_file(fname, percent)

            self.download_file(filename, callback=file_cb)
            downloaded_files += 1

            # Gesamtfortschritt
            if callback_global:
                percent_total = int(downloaded_files / total_files * 100)
                callback_global(downloaded_files, total_files, percent_total)

        return True
