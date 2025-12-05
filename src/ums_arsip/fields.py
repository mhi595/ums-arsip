from django.db.models import FileField
from .storage import ArsipStorage


class ArsipFileField(FileField):
    """
    Alur proses penggunaan:
        1. Buat pada model:
            filesk_arsip = ArsipFileField(
                meta={
                    "deskripsi": lambda o: "File SK Kenaikan Pangkat/golongan {}".format(getattr(getattr(o, 'ckarid', None), 'tloginname', '')),
                    "username": lambda obj: obj.ckarid.tloginname if obj and getattr(obj, "ckarid", None) else settings.DEFAULT_ARSIP_USERNAME
                }
            )
        2. pada settings.py, isi DEFAULT_ARSIP_USERNAME, DEFAULT_ARSIP_LEMBAGA, DEFAULT_ARSIP_JENIS, DEFAULT_ARSIP_SIFAT sesuai kebutuhan.
        3. meta pada Model digunakan untuk mengisi atribut pada UploadedFile yang dikirim ke ArsipStorage.
        4. use_innername pada meta Model dapat diisi False untuk menonaktifkan penggunaan innername (misal untuk file baru yang tidak perlu update).
        5. Pada ArsipStorage, atribut-atribut tersebut akan digunakan untuk mengisi data pada API Arsip.
        6. prepare_uploaded_file pada ArsipStorage dapat digunakan untuk menimpa atribut yang sudah dideskripsikan pada meta Model.
    """

    def __init__(self, *args, meta=None, **kwargs):
        """
        meta = {
            "username": lambda instance: instance.tloginname,
            "deskripsi": lambda instance: f"KTP {instance.tloginname}",
            "jenis": 5,
            "sifat": 1,
            "lembaga": "lmbg1149",
        }
        """
        self.meta = meta or {}
        kwargs["storage"] = ArsipStorage()
        super().__init__(*args, **kwargs)

    def save_form_data(self, instance, data):
        """
        Saves the uploaded file data to the specified instance.

        This method is called with the uploaded file from request.FILES
        before Django processes it for storage. It allows for modification
        of the uploaded file's attributes based on the provided metadata.

        Parameters:
            instance: The model instance to which the uploaded file is associated.
            data: The uploaded file data (an instance of UploadedFile) that needs to be saved.

        Modifications:
        - Attaches metadata to the UploadedFile instance unless it has been locked.
        - Handles the 'innername' attribute based on the 'use_innername' setting in metadata.
        - If 'use_innername' is enabled, it retrieves the old file name from the existing instance.
        - Ensures that 'innername' is removed if 'use_innername' is disabled.

        Returns:
            None
        """
        if data:
            # data is the actual UploadedFile Django will send to storage._save()
            uploaded = data

            # ---- attach meta to UploadedFile ----
            if not getattr(uploaded, "_prepare_lock", False): # jika sudah dilock di prepare_uploaded_file ArsipStorage, jangan diubah lagi
                for key, val in self.meta.items():
                    if key == "use_innername":
                        continue
                    setattr(uploaded, key, val(instance) if callable(val) else val)

            # ---- handle innername only if use_innername != False ----
            use_innername = self.meta.get("use_innername", True)

            if use_innername:
                # ---- detect old file ----
                try:
                    old_instance = instance.__class__.objects.get(pk=instance.pk)
                    old_file = getattr(old_instance, self.attname)
                    old_name = old_file.name if old_file else None
                except instance.__class__.DoesNotExist:
                    old_name = None

                setattr(uploaded, "innername", old_name)
            else:
                # Make sure innername doesn't exist if disabled
                if hasattr(uploaded, "innername"):
                    delattr(uploaded, "innername")

        # IMPORTANT: pass modified data forward
        super().save_form_data(instance, data)