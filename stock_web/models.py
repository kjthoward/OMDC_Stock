from django.db import models, transaction
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import F
from django.apps import apps
from django.conf import settings
from calendar import monthrange
import datetime
import pdb
import itertools


from .email import send, EMAIL


#Check if should be set to True. True would mean that whenever anyone gets an account
#made they will need to change password on first login. Useful as allows accounts
#to be made by admin with e.g "password" but could be annoying if user is there
#when acount gets made and sets their own password...
class ForceReset(models.Model):
    def __str__(self):
        return "Toggle Reset for {}".format(self.user)
    class Meta:
        verbose_name_plural = "Force Password Resets"
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    force_password_change = models.BooleanField(default=True)
    emailed=models.BooleanField(default=False)

#automatically adds user to ForceReset table upon creation
#if not done will give errors when trying to do checks
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        ForceReset.objects.create(user=instance)
    if instance.email!="":
        USER=ForceReset.objects.get(user=instance)
        if USER.emailed==False:
            subject="Stock Database account created"
            text="<p>An account on the Stock Database has been created with the following details:<br><br>"
            text+="Username: {}<br><br>".format(instance.username)
            text+="Password: stockdb1<br><br>"
            text+="NOTE - you will be required to change this password when you first log in.<br><br>"
            if EMAIL==True:
                try:
                    send(subject,text, instance.email)
                    USER.emailed=True
                    USER.save()
                except:
                    print("EMAIL ERROR")
                    pass

class Suppliers(models.Model):
    def __str__(self):
        return self.name
    name = models.CharField(max_length=50, unique=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Suppliers"

    @classmethod
    def create(cls, name):
        supplier = cls.objects.create(name=name)
        return supplier

class Projects(models.Model):
    def __str__(self):
        return self.name
    name = models.CharField(max_length=50, unique=True)
    is_active=models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Projects"

    @classmethod
    def create(cls, name):
        project = cls.objects.create(name=name)
        return project

##class Storage(models.Model):
##    def __str__(self):
##        return self.name
##    class Meta:
##        verbose_name_plural = "Storage"
##    name = models.CharField(max_length=20, unique=True)

class Reagents(models.Model):
    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural = "Reagents"
        ordering = ["name"]
    name = models.CharField(max_length=100, unique=True)
    cat_no = models.CharField(max_length=20, blank=True, null=True, verbose_name=u"Catalogue Number")
    supplier_def = models.ForeignKey(Suppliers, on_delete=models.PROTECT, verbose_name=u"Default Supplier")
    #storage = models.ForeignKey(Storage, on_delete=models.PROTECT, blank=True, null=True)
    count_no=models.PositiveIntegerField(default=0)
    min_count=models.PositiveIntegerField(verbose_name=u"Minimum Stock Level")
    recipe=models.ForeignKey("Recipe", on_delete=models.PROTECT, blank=True, null=True)
    track_vol=models.BooleanField(default=False, verbose_name=u"Tick to enable volume tracking for this reagent")
    is_active=models.BooleanField(default=True)

    @classmethod
    def create(cls, values):
        with transaction.atomic():
            reagent=cls(**values)
            reagent.save()
            return reagent

class Internal(models.Model):
    def __str__(self):
        return self.batch_number
    class Meta:
        verbose_name_plural = "Stock Numbers"
    batch_number = models.CharField(max_length=4, unique=True)
    @classmethod
    def create(cls):
        internal_id=cls.objects.create(batch_number="".join(next(possibles)))
        return internal_id

#Ordered (for dev so can see increments)
##first=['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
##second=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9','A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
##third=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9','A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
##fourth=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9','A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
#Random for production so doesn't appear sequenctial
first=['J', 'F', 'G', 'U', 'M', 'A', 'Y', 'R', 'E', 'H', 'B', 'K', 'N', 'W', 'C', 'V', 'Z', 'P', 'S', 'X', 'D', 'L', 'T', 'Q']
second=['1', 'K', '6', 'U', 'W', '8', 'J', '9', 'F', 'C', 'N', 'B', '0', 'L', '2', '4', 'Z', 'X', 'M', 'G', '3', 'R', '7', 'E', '5', 'D', 'S', 'H', 'V', 'P', 'T', 'Y', 'A', 'Q']
third=['9', 'A', 'B', 'P', 'Q', 'G', 'V', '3', 'C', '5', 'T', 'J', 'D', 'K', '1', 'H', '6', 'W', 'E', 'S', '2', 'M', 'Z', 'X', 'R', 'U', 'Y', '7', '4', 'F', '8', '0', 'N', 'L']
fourth=['X', 'R', 'W', '7', '4', 'B', 'Y', '0', 'D', '8', 'Z', 'Q', 'N', 'C', 'E', 'J', 'V', '1', '5', 'S', '6', 'F', 'P', 'T', 'G', 'M', '2', '3', 'L', 'H', 'A', '9', 'K', 'U']
#max number of items is 943,296, will break after this point, then would need to either reset or add digit
#adding digit would require change to model max_length
possibles=itertools.product(first,second,third,fourth)
try:
    new_id=Internal.objects.last().id
except:
    new_id=0
for _ in range(new_id):
    next(possibles)

class Validation(models.Model):
    def __str__ (self):
        return "{} {}".format(self.val_run, self.val_date.strftime("%d/%m/%y"))
    val_date=models.DateField(null=True, blank=True)
    val_run=models.CharField(max_length=25)
    val_user=models.ForeignKey(User, limit_choices_to={"is_active":True}, on_delete=models.PROTECT)

    @classmethod
    def new(cls, date, run, user):
        try:
            val_id=cls.objects.get(val_date=date, val_run=run, val_user=user)
        except:
            val_id=cls.objects.create(val_date=date, val_run=run, val_user=user)
        return val_id

class Recipe(models.Model):
    def __str__(self):
        return self.name
    name = models.CharField(max_length=100, unique=True)
    comp1=models.ForeignKey(Reagents, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"component 1", related_name="component1")
    comp2=models.ForeignKey(Reagents, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"component 2", related_name="component2")
    comp3=models.ForeignKey(Reagents, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"component 3", related_name="component3")
    comp4=models.ForeignKey(Reagents, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"component 4", related_name="component4")
    comp5=models.ForeignKey(Reagents, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"component 5", related_name="component5")
    comp6=models.ForeignKey(Reagents, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"component 6", related_name="component6")
    comp7=models.ForeignKey(Reagents, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"component 7", related_name="component7")
    comp8=models.ForeignKey(Reagents, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"component 8", related_name="component8")
    comp9=models.ForeignKey(Reagents, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"component 9", related_name="component9")
    comp10=models.ForeignKey(Reagents, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"component 10", related_name="component10")
    reagent=models.ForeignKey(Reagents, blank=True, null=True, on_delete=models.PROTECT, verbose_name=u"Reagent ID", related_name="Reagent_ID")
    shelf_life=models.PositiveIntegerField(verbose_name=u"Shelf Life (Months)")
    track_vol=models.BooleanField(default=False, verbose_name=u"Tick to enable volume tracking for this recipe")

    @classmethod
    def create(cls, values):
        with transaction.atomic():
            minstock=values["number"]
            del(values["number"])
            recipe=cls(**values)
            recipe.save()
            try:
                values={"name":values["name"],
                        "supplier_def":Suppliers.objects.get(name="Internal"),
                        "recipe":recipe,
                        "min_count":minstock,
                        "track_vol":values["track_vol"],
                        }
            except:
                values={"name":values["name"],
                        "supplier_def":Suppliers.create(name="Internal"),
                        "recipe":recipe,
                        "min_count":minstock,
                        "track_vol":values["track_vol"],
                        }
            recipe.reagent=(Reagents.create(values))
            recipe.save()


    def length(self):
        count=0
        for k,v in Recipe.objects.filter(pk=self.id).values().first().items():
            if "comp" in k and v is not None:
                count+=1
        return count

    def liststock(self):
        possibles=[]
        for k,v in Recipe.objects.filter(pk=self.id).values().first().items():
            if "comp" in k and v is not None:
                inv_id=v
                in_stock=Inventory.objects.select_related("supplier","reagent","internal").filter(reagent_id=inv_id,finished=False)
                for stock in in_stock:
                    possibles+=[stock]
        return possibles


class Inventory(models.Model):
    def __str__(self):
        return "{}, Lot:{}, Batch:{}, Project:{}".format(self.reagent.name, self.lot_no, self.internal,self.project)
    class Meta:
        verbose_name_plural = "Inventory Items"
    reagent=models.ForeignKey(Reagents,on_delete=models.PROTECT)
    GOOD="GD"
    DAMAGED_OK="DU"
    UNUSABLE="UN"
    INHOUSE="NA"
    CONDITION_CHOICES=[
        (GOOD,"Good"),
        (INHOUSE,"N/A, Made in House"),
        (DAMAGED_OK,"Damaged - Usable"),
        (UNUSABLE,"Damaged - Not Usable"),
        ]
    internal=models.ForeignKey(Internal, on_delete=models.PROTECT)
    supplier=models.ForeignKey(Suppliers, on_delete=models.PROTECT)
    lot_no=models.CharField(max_length=50, verbose_name=u"Lot Number")
    sol=models.ForeignKey("Solutions", on_delete=models.PROTECT, blank=True, null=True)
    po=models.CharField(max_length=20, verbose_name=u"Purchase Order")
    date_rec=models.DateField(default=datetime.date.today, verbose_name=u"Date Received")
    cond_rec=models.CharField(max_length=2, choices=CONDITION_CHOICES, default=GOOD, verbose_name=u"Condition Received")
    rec_user=models.ForeignKey(User, limit_choices_to={"is_active":True}, on_delete=models.PROTECT, related_name="1+")
    date_exp=models.DateField(verbose_name=u"Expiry Date")
    project=models.ForeignKey("Projects", on_delete=models.PROTECT, blank=True, null=True)
    date_op=models.DateField(null=True, blank=True)
    is_op=models.BooleanField(default=False)
    op_user=models.ForeignKey(User, limit_choices_to={"is_active":True}, on_delete=models.PROTECT, related_name="2+", blank=True, null=True)
    val=models.ForeignKey(Validation, null=True, blank=True, on_delete=models.PROTECT)
    date_fin=models.DateField(null=True, blank=True, verbose_name=u"Date Finished")
    finished=models.BooleanField(default=False)
    fin_user=models.ForeignKey(User, limit_choices_to={"is_active":True}, on_delete=models.PROTECT, related_name="3+", blank=True, null=True)
    fin_text = models.CharField(max_length=100, blank=True, null=True, verbose_name=u"Finished Reason")
    vol_rec=models.PositiveIntegerField(verbose_name=u"Volume Received (µl)", blank=True, null=True)
    current_vol=models.PositiveIntegerField(verbose_name=u"Current Volume (µl)", blank=True, null=True)
    last_usage=models.ForeignKey('VolUsage', blank=True, null=True, on_delete=models.PROTECT)
    witness=models.ForeignKey(User, limit_choices_to={"is_active":True}, on_delete=models.PROTECT, related_name="4+", blank=True, null=True)
    def days_remaining(self):
        return (self.date_exp-datetime.date.today()).days

    @classmethod
    def create(cls, values, user):
        if "witness" not in values.keys():
            values["witness"]=None
        values["rec_user"]=user
        if "num_rec" in values.keys():
            amount=values["num_rec"]
            del(values["num_rec"])
        else:
            values["current_vol"]=values["vol_rec"]
            amount=1
        with transaction.atomic():
            try:
                values["val_id"]=Inventory.objects.filter(reagent=values["reagent"].id, lot_no=values["lot_no"],val_id__gte=0).first().val_id
            except: pass
            if "~" in values["reagent"].name:
                try:

                    values["val_id"]=Validation.objects.get(val_date=values["date_rec"], val_run="NOT_TO_BE_TESTED").pk
                except:
                    values["val_id"]=Validation.objects.create(val_date=values["date_rec"], val_run="NOT_TO_BE_TESTED",val_user_id=user.id).pk

            internals=[]
            for _ in range(amount):
                inventory=cls(**values)
                inventory.internal=Internal.create()
                internals+=[inventory.internal.batch_number]
                if inventory.lot_no=="":
                    inventory.lot_no=inventory.internal.batch_number
                inventory.save()
            reagent=Reagents.objects.get(id=values["reagent"].id)
            if "vol_rec" in values.keys():
                reagent.count_no=F("count_no")+values["vol_rec"]
            else:
                reagent.count_no=F("count_no")+amount
            reagent.save()
            return internals

    @classmethod
    def open(cls, values, item, user):
        with transaction.atomic():
            reagent=Inventory.objects.get(id=item).reagent
            if reagent.track_vol==False:
                reagent.count_no=F("count_no")-1
                reagent.save()
            invitem=Inventory.objects.get(id=item)
            invitem.date_op=values["date_op"]
            invitem.op_user=user
            invitem.is_op=True
            invitem.save()

    @classmethod
    def take_out(cls, vol, item, user, date=datetime.datetime.now().date(), sol=None):
        with transaction.atomic():
            invitem=Inventory.objects.get(id=item)
            start_vol=invitem.current_vol
            invitem.current_vol=F("current_vol")-vol
            invitem.save()
            invitem.refresh_from_db()
            if invitem.current_vol==0:
                values={"date_fin":date,
                        "fin_text":"",
                        "vol":vol}
                invitem.finish(values, item, user)
            else:
                reagent=Reagents.objects.get(pk=invitem.reagent_id)
                reagent.count_no=F("count_no")-vol
                reagent.save()
            VolUsage.use(item, start_vol,invitem.current_vol, vol,
                        user, sol, date)
    @classmethod
    def validate(cls, values, reagent_id, lot, user):

        with transaction.atomic():
            val=Validation.new(values["val_date"], values["val_run"].upper(), user)
            #bulk_update(updates.values(),[item.val_id=val])
            Inventory.objects.filter(reagent=reagent_id, lot_no=lot).update(val_id=val)

            #for item in items:
            #    item.val_id=val
            #Inventory.objects.bulk_update(items,['val_id'])
    @classmethod
    def finish(cls, values, item, user):
        with transaction.atomic():
            invitem=Inventory.objects.get(id=item)
            invitem.fin_user=user
            invitem.fin_text=values["fin_text"]
            invitem.date_fin=values["date_fin"]
            invitem.finished=True

            reagent=Inventory.objects.get(id=item).reagent
            if reagent.track_vol==False and invitem.is_op==False:
                reagent.count_no=F("count_no")-1
                invitem.save()
                reagent.save()

            elif reagent.track_vol==False and invitem.is_op==True:
                invitem.save()

            elif reagent.track_vol==True:

                if invitem.current_vol!=0:
                    use=VolUsage.use(item,invitem.current_vol,0,invitem.current_vol,user,None,values["date_fin"])
                    invitem.last_usage=use
                if "vol" in values.keys():
                    reagent.count_no=F("count_no")-values["vol"]
                else:
                    reagent.count_no=F("count_no")-invitem.current_vol
                reagent.save()
                invitem.current_vol=0
                invitem.save()


class VolUsage(models.Model):
    class Meta:
        verbose_name_plural = "Reagent Volume Usage"
    item=models.ForeignKey(Inventory, blank=True, null=True, on_delete=models.PROTECT)
    start=models.PositiveIntegerField()
    end=models.PositiveIntegerField()
    used=models.PositiveIntegerField()
    date=models.DateField(default=datetime.date.today)
    user=models.ForeignKey(User, on_delete=models.PROTECT)
    sol=models.ForeignKey('Solutions', on_delete=models.PROTECT,  blank=True, null=True)

    @classmethod
    def use(cls, item, start_vol, end_vol, volume, user, sol, date=datetime.datetime.now().date()):
        invitem=Inventory.objects.get(pk=int(item))
        use=VolUsage.objects.create(item=invitem, start=start_vol,
                                    end=end_vol, used=volume,
                                    date=date, user=user, sol=sol)
        invitem.last_usage=use
        invitem.save()
        return use
class Solutions(models.Model):
    class Meta:
        verbose_name_plural = "Solutions"
    recipe=models.ForeignKey(Recipe, limit_choices_to={"is_active":True}, on_delete=models.PROTECT)
    comp1=models.ForeignKey(Inventory, blank=True, null=True, limit_choices_to={"finished":False}, on_delete=models.PROTECT, related_name="comp1")
    comp2=models.ForeignKey(Inventory, blank=True, null=True, limit_choices_to={"finished":False}, on_delete=models.PROTECT, related_name="comp2")
    comp3=models.ForeignKey(Inventory, blank=True, null=True, limit_choices_to={"finished":False}, on_delete=models.PROTECT, related_name="comp3")
    comp4=models.ForeignKey(Inventory, blank=True, null=True, limit_choices_to={"finished":False}, on_delete=models.PROTECT, related_name="comp4")
    comp5=models.ForeignKey(Inventory, blank=True, null=True, limit_choices_to={"finished":False}, on_delete=models.PROTECT, related_name="comp5")
    comp6=models.ForeignKey(Inventory, blank=True, null=True, limit_choices_to={"finished":False}, on_delete=models.PROTECT, related_name="comp6")
    comp7=models.ForeignKey(Inventory, blank=True, null=True, limit_choices_to={"finished":False}, on_delete=models.PROTECT, related_name="comp7")
    comp8=models.ForeignKey(Inventory, blank=True, null=True, limit_choices_to={"finished":False}, on_delete=models.PROTECT, related_name="comp8")
    comp9=models.ForeignKey(Inventory, blank=True, null=True, limit_choices_to={"finished":False}, on_delete=models.PROTECT, related_name="comp9")
    comp10=models.ForeignKey(Inventory, blank=True, null=True, limit_choices_to={"finished":False}, on_delete=models.PROTECT, related_name="comp10")
    creator_user=models.ForeignKey(User, limit_choices_to={"is_active":True}, on_delete=models.PROTECT)
    date_created=models.DateField(default=datetime.date.today)

    @classmethod
    def create(cls, rec, comp_ids, vols_used, vol_made, user, witness):
        with transaction.atomic():
            ids=set(comp_ids)
            comps = apps.get_model("stock_web", "Inventory").objects.filter(id__in=ids)
            comps_dict={}
            for i, comp in enumerate(comps, start=1):
                comps_dict["comp{}".format(i)]=comp
                if comp.is_op==False:
                    values={"date_op":comp.date_rec,
                          }
                    comp.open(values, comp.pk, user)

            solution=cls.objects.create(recipe=rec, creator_user=user, date_created=datetime.datetime.today(),**comps_dict)
            solution.save()
            #Shelf life/Expiry calculations
            start_day=int(datetime.datetime.today().strftime("%d"))
            start_month=int(datetime.datetime.today().strftime("%m"))+rec.shelf_life
            start_year=int(datetime.datetime.today().strftime("%Y"))
            #Checks that adding shelf life to current month doesn't go over 12 months, incremements year if it does
            #while not if used as could be longer than 1 year expiry so need to do multiple checks
            while start_month>12:
                start_year+=1
                start_month-=12
            #checks that the day is valid, goes to 1st of next month if it is not
            #e.g making something on 30th Jan with 1 month shelf life gives 30th Feb which is not valid,
            #would become 1st March in this case
            if start_day>monthrange(start_year,start_month)[1]:
                start_day=1
                start_month+=1
                #rechecks that adding 1 to the month for invalid day hasn't ticked over a year
                if start_month>12:
                    start_year+=1
                    start_month-=12
            EXP_DATE=datetime.datetime.strptime("{}/{}/{}".format(start_day,start_month,start_year),"%d/%m/%Y")
            values={"date_rec":datetime.datetime.today(),
                    "cond_rec":"NA",
                    "date_exp":EXP_DATE,
                    "sol":solution,
                    "po":"N/A",
                    "project":Projects.objects.get(name="INTERNAL"),
                    "reagent":rec.reagent,
                    "supplier":Suppliers.objects.get(name="Internal"),
                    "witness":witness,
                    }
            if vol_made=="":
                values["num_rec"]=1
            else:
                values["vol_rec"]=vol_made
                for item, vol in vols_used.items():
                    Inventory.take_out(vol,item,user,sol=solution)
            return Inventory.create(values,user)
    def list_comp(self):
        comps=[]
        for i in range(1,11):
            if eval("self.comp{}".format(i)) is not None:
                comps+=[eval("self.comp{}".format(i))]
        return comps
