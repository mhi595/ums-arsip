import requests
from django.conf import settings
from django.core.files.storage import Storage
from django.db.models import Model
from django.core.files import File


class ArsipStorage(Storage):
    """
    Custom storage for uploading files to ARSIP.
    """

    api_url = settings.ARSIP_URL + "/serve/v2/"
    auth = ('alkindi', settings.ARSIP_PASS)

    def _save(self, name, content):
        """
        Called automatically when saving a FileField.
        Detect: if existing file name exists -> PUT
                else -> POST
        """
        # Detect if updating existing file
        innername = getattr(content, "innername", None)
        multipart_data = {
            "file": (name, content),
            # "deskripsi": (None, name),
            "deskripsi": (None, getattr(content, "deskripsi", name)),
            "sifat": (None, getattr(content, "sifat", settings.DEFAULT_ARSIP_SIFAT)),
            "jenis": (None, getattr(content, "jenis", settings.DEFAULT_ARSIP_JENIS)),
            "username": (None, getattr(content, "username", settings.DEFAULT_ARSIP_USERNAME)),
            "lembaga": (None, getattr(content, "lembaga", settings.DEFAULT_ARSIP_LEMBAGA)),
        }

        # ----- UPDATE file -----
        if innername:
            multipart_data["innername"] = (None, innername)
            resp = requests.put(self.api_url, auth=self.auth, files=multipart_data, timeout=20)
            if resp.status_code == 202:
                return innername
            raise Exception("Gagal update file ke Arsip (PUT)")

        # ----- NEW file -----
        resp = requests.post(self.api_url, auth=self.auth, files=multipart_data, timeout=20)
        if resp.status_code == 201:
            data = eval(resp.json())
            return data["nama"]

        raise Exception("Gagal upload file ke Arsip (POST)")

    def url(self, name):
        """
        Return accessible URL from stored filename.
        """
        return "{}berkas/{}".format(settings.ARSIP_URL, name)

    def exists(self, name):
        """
        Always return False so storage always uploads.
        """
        return False

    @staticmethod
    def prepare_uploaded_file(instance: Model, field_name: str, uploaded_file: File, multipart_data: dict) -> File:
        """
        Prepare an uploaded file by attaching metadata before saving it to the instance.

        Parameters:
            instance (Model): The model instance to which the file is being attached.
            field_name (str): The name of the field in the model where the file will be stored.
            uploaded_file (File): The file object that has been uploaded.
            multipart_data (dict, optional): allowed_fields = ["deskripsi", "sifat", "jenis", "username", "lembaga"]

        Returns:
            File: The modified uploaded file with attached metadata.

        Example:
            upload_filektp = request.FILES.get('filektp_url', None)
            if upload_filektp:
                form1.fields['filektp_url'].initial = ArsipStorage.prepare_uploaded_file(
                    instance=staf,
                    field_name='filektp_url',
                    uploaded_file=upload_filektp,
                    multipart_data={"deskripsi": "File KTP {} dari form".format(str(staf.tloginname)), "username": request.user.username}
                )
        """
        # Old file name
        old_file = getattr(instance, field_name)
        old_name = old_file.name if old_file else None
        # innername
        uploaded_file.innername = old_name
        # Fields allowed to be injected into uploaded_file
        allowed_fields = ["deskripsi", "sifat", "jenis", "username", "lembaga"]
        # Inject metadata cleanly
        for key in allowed_fields:
            value = multipart_data.get(key)
            if value not in (None, ""):
                setattr(uploaded_file, key, value)
                setattr(uploaded_file, "_prepare_lock", True) # lock data to prevent double modification
        # return modified file
        return uploaded_file
