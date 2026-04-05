from pathlib import Path
import requests


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# 先留空，等你把 NSW sales 下载链接拿到后替换
NSW_SALES_URL = ""


def download_file(url: str, output_filename: str) -> Path:
    if not url:
        raise ValueError("NSW_SALES_URL is empty. Please set the official download URL first.")

    output_path = DATA_DIR / output_filename

    with requests.get(url, stream=True, timeout=60) as response:
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    return output_path


if __name__ == "__main__":
    print("Set NSW_SALES_URL to the official bulk sales file URL before running.")