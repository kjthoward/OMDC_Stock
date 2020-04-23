from django.db import transaction
from django.contrib.auth.models import User, Group
from .models import ForceReset, Suppliers, Reagents, Internal, Validation, Recipe, Inventory, Solutions, VolUsage

def PRIME():
    with transaction.atomic():
        User_Mod = Group.objects.create(name="User_Mod")
        perms=['13','14','16','8','5','6','9','10','12']
        for p in perms:
            User_Mod.permissions.add(p)
        Non_SU_Admin = Group.objects.create(name="Non_SU_Admin")
        perms2=['1','2','4','5','6','8','9','10','12','13','14','16','17','18','19','21','22','23','24']
        for p2 in perms2:
            Non_SU_Admin.permissions.add(p2)
        #password fine in here as after first log on required to change it
        user = User.objects.create_user("Admin", "", "password")
        user.first_name = ""
        user.last_name = ""
        user.is_superuser=True
        user.is_staff=True
        user.save()
