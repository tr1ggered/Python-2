import asyncio
import prettytable
from requests import get
from aioconsole import ainput
import os

#проверка валидности пути
def is_valid_path(path):
    test_file = os.path.join(path, 'write_test')
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('test')
        os.remove(test_file)
        return True
    except (PermissionError, FileNotFoundError, NotADirectoryError, OSError):
        return False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

async def download_image(url, save_dir, results):
    try:
        response = await asyncio.to_thread(get, url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            filename = os.path.join(save_dir, os.path.basename(url))
            with open(filename, "wb") as f:
                f.write(response.content)
            results.append((url, "Success"))
        else:
            results.append((url, "Error"))
    except Exception:
        results.append((url, "Error"))
#
async def iostream(save_dir, results, tasks):
    while True:
        url = await ainput('Enter image URL (empty line to stop): ')
        url = url.strip()
        if url == "":
            break
        task = asyncio.create_task(download_image(url, save_dir, results))
        tasks.append(task)

#
async def main():
    while True:
        save_dir = await ainput('Enter directory to save images: ')
        save_dir = save_dir.strip()
        if is_valid_path(save_dir):
            break
        print("Invalid path or no access. Try again.")
    results = []
    tasks = []
    await iostream(save_dir, results, tasks)
    incomplete = [t for t in tasks if not t.done()]
    if incomplete:
        print(f"Waiting for {len(incomplete)} download(s) to finish...")
    await asyncio.gather(*tasks)
    table = prettytable.PrettyTable()
    table.field_names = ["Link", "Status"]
    for url, status in results:
        table.add_row([url, status])
    print(table)

if __name__ == '__main__':
    asyncio.run(main())