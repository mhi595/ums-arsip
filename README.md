# UMS Arsip for Django

`ums-arsip` is a Django storage backend and custom `FileField`
designed to integrate seamlessly with the **ARSIP API UMS** used for
uploading, updating, and retrieving stored files.

This package provides:

✔ A custom `ArsipStorage` class that automatically handles **POST (new upload)** and **PUT (update)** based on metadata\
✔ A powerful `ArsipFileField` with `meta={}` options for dynamic metadata injection\
✔ A helper method `prepare_uploaded_file()` for advanced control\
✔ A clean API that plugs into Django models with zero hassle

## 🚀 Features
- 🔄 Automatic PUT / POST detection
    - Updates existing files if innername is present, otherwise uploads a new file.
- 📝 Dynamic metadata injection
    - Supply metadata using lambdas or static values via meta={} in ArsipFileField.
- 🧩 Drop-in FileField replacement
    - Works the same as Django’s built-in FileField.
- 🪝 Full control over upload preparation
    - Use prepare_uploaded_file() when you want to set metadata directly in views/forms.
- 🔐 Supports Django settings for defaults
    - Uses project-level settings like username, description, sifat, jenis, etc.

## Installation

``` bash
pip install ums-arsip
```

## Required Django Settings

``` python
ARSIP_URL = "https://arsip.example.com"
ARSIP_PASS = "password_or_token"

DEFAULT_ARSIP_USERNAME = "default-user"
DEFAULT_ARSIP_LEMBAGA = "default-lembaga"
DEFAULT_ARSIP_JENIS = 1
DEFAULT_ARSIP_SIFAT = 1
```

## Basic Usage

### 1️. Import ArsipFileField in your model:
```python
from django.db import models
from ums_arsip import ArsipFileField
```

### 2. Add it to your model:
``` python
from django.db import models
from ums_arsip import ArsipFileField

class Staff(models.Model):
    tloginname = models.CharField(max_length=64)

    filektp_arsip = ArsipFileField(
        db_column='filektp_arsip',
        blank=True, null=True,
        meta={
            "deskripsi": lambda obj: "File KTP {}".format(getattr(obj, 'tloginname', None)),
            "username": lambda obj: obj.ckarid.tloginname if obj and getattr(obj, "ckarid", None) else settings.DEFAULT_ARSIP_USERNAME
        }
    )
```
- The field will:
    - Attach metadata (deskripsi, username, etc.)
    - Track old files for update (PUT)
    - Upload new files with correct attributes (POST)

## 🧠 Understanding meta={}
- ArsipFileField accepts a meta dictionary to control metadata passed to ARSIP API.
- Example:
    ```python
    meta = {
        "deskripsi": lambda instance: f"Dokumen milik {instance.nama}",
        "username": "static_username",
        "jenis": 5,
        "sifat": 1,
        "lembaga": "org-id",
        "use_innername": False,
    }
    ```
- Supported keys:
    | Field           | Type                | Description                            |
    | --------------- | ------------------- | -------------------------------------- |
    | `deskripsi`     | str / λ             | File description sent to ARSIP         |
    | `username`      | str / λ             | Username performing upload             |
    | `jenis`         | int                 | File type code                         |
    | `sifat`         | int                 | Confidentiality level                  |
    | `lembaga`       | str                 | Organization ID in ARSIP               |
    | `use_innername` | bool (default=True) | Whether to track old file for updating |
- Lambda behavior
    - If value is callable (lambda or function), it receives the model instance:
        ```python
        "deskripsi": lambda obj: f"DOC for {obj.name}"
        ```

## 📤 Using prepare_uploaded_file() in Views (Advanced)
Sometimes you want to override metadata directly in the view.
``` python
from ums_arsip.storage import ArsipStorage

def upload_view(request, pk):
    staff = Staff.objects.get(pk=pk)
    upload = request.FILES.get("file_ktp")

    if upload:
        prepared = ArsipStorage.prepare_uploaded_file(
            instance=staff,
            field_name="file_ktp",
            uploaded_file=upload,
            multipart_data={
                "deskripsi": f"File KTP {staff.tloginname} dari form",
                "username": request.user.username
            }
        )
        staff.file_ktp = prepared
        staff.save()
```
This bypasses the automatic meta={} logic and gives full manual control.

## 🧱 How Upload Logic Works

### POST (New File)
- Triggered if the uploaded file has no innername attribute.
- Response must include:
    ```json
    {"nama": "file12345.pdf"}
    ```

### PUT (Update Existing File)
- Triggered when:
    ```json
    uploaded_file.innername = "old_file_name.pdf"
    ```
- Django attaches innername automatically when:
    - The model instance already has a file.
    - meta["use_innername"] is not set to False.


## 🔗 Returned File Path
- Every saved file becomes accessible with:
    ```
    <ARSIP_URL>/berkas/<filename>
    ```
- Example:
    ```python
    instance.file_ktp.url
    # → https://arsip.example.com/berkas/abc123.pdf
    ```

## ⚡ API Reference

### ArsipStorage
- Methods:
    | Method                    | Description                          |
    | ------------------------- | ------------------------------------ |
    | `_save(name, content)`    | Uploads or updates file              |
    | `url(name)`               | Returns full public URL              |
    | `exists(name)`            | Always returns False (forces upload) |
    | `prepare_uploaded_file()` | Injects metadata & innername         |

### ArsipFileField
- Drop-in replacement for Django’s FileField.
- Automatically:
    - attaches metadata
    - detects updates
    - handles innername toggling

## 🐞 Troubleshooting
- Failed to upload file to Arsip (POST)
    - Possible reasons:
        - ARSIP_URL is wrong
        - ARSIP_PASS invalid
        - Multipart fields missing
- innername is None but file should update
    - Set:
        ```python
        meta={"use_innername": True}
        ```
- Overwritten metadata not taking effect
    - You may have used:
        ```python
            prepare_uploaded_file()
        ```

## 📜 Changelog
- v0.1.0
    - Initial release
    - Includes ArsipStorage & ArsipFileField
    - Metadata injection system
    - PUT / POST automatic detection
    - prepare_uploaded_file() helper


## 📄 License

MIT License

Copyright (c) 2025 Muhammad Hammam Islami

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.