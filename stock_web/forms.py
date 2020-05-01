import datetime
from django import forms
from django.db.models import F
from django.contrib.auth.models import User
from django_select2.forms import Select2Widget
from .models import Suppliers, Reagents, Internal, Recipe, Inventory, Projects

class LoginForm(forms.Form):
    username = forms.CharField(max_length=20, widget=forms.TextInput(attrs={"autocomplete": "off"}))
    password = forms.CharField(max_length=20, widget=forms.PasswordInput(attrs={"autocomplete": "off"}))
#sets width of all Select2Widget search boxes
Select2Widget=Select2Widget(attrs={"style": "width:12.5em"})

#custom select date widget (based off of default), allows you to set a custom data range to display
class MySelectDateWidget(forms.SelectDateWidget):
    def get_context(self, name, value, attrs):
        old_state = self.is_required
        self.is_required = False
        context = super(MySelectDateWidget, self).get_context(name, value, attrs)
        self.is_required = old_state
        return context

class NewInvForm1(forms.ModelForm):
    reagent=forms.ModelChoiceField(queryset = Reagents.objects.all().exclude(is_active=False).order_by("name"), label="Reagent", widget=Select2Widget)

    class Meta:
        model = Inventory
        fields= ("reagent",)
    def clean(self):
        super(NewInvForm1, self).clean()
        errors=[]
        item=Reagents.objects.get(pk=self.data["reagent"])
        if item.recipe is not None:
            for i in range(1,item.recipe.length()+1):
                if Reagents.objects.get(pk=eval('item.recipe.comp{}.id'.format(i))).count_no==0:
                    errors+=[forms.ValidationError("There is no {} in stock".format(eval('item.recipe.comp{}.name'.format(i))))]
            if errors:
                raise forms.ValidationError(errors)
        #filters out recipes from inventory selection form
##    def __init__(self, *args, **kwargs):
##        super(NewInvForm1, self).__init__(*args, **kwargs)
##        self.fields["reagent"].queryset=Reagents.objects.filter(recipe_id=None)
class NewInvForm(forms.ModelForm):
    num_rec=forms.IntegerField(min_value=1, label="Number Received")
    class Meta:
        model = Inventory
        fields = ("reagent", "supplier", "lot_no", "cond_rec", "date_rec", "po", "date_exp", "project")
        widgets = {"supplier":Select2Widget,
                   "project":Select2Widget,
                   "lot_no":forms.Textarea(attrs={"style": "height:2em;"}),
                   "date_rec":MySelectDateWidget(years=range(datetime.datetime.today().year-1,datetime.datetime.today().year+1)),
                   "date_exp":MySelectDateWidget(years=range(datetime.datetime.today().year-1,datetime.datetime.today().year+20)),
                   "reagent":forms.HiddenInput(),
                   "vol_rec":forms.HiddenInput(),
                   "current_vol":forms.HiddenInput()}

    def clean(self):
        super(NewInvForm, self).clean()
        if self.cleaned_data["date_exp"]<self.cleaned_data["date_rec"]:
            self.add_error("date_exp", forms.ValidationError("Expiry date occurs before received date"))
        elif self.cleaned_data["date_rec"]>datetime.date.today():
            self.add_error("date_rec", forms.ValidationError("Date received occurs in the future"))
    def __init__(self, *args, **kwargs):
        super(NewInvForm, self).__init__(*args, **kwargs)
        self.fields["supplier"].queryset=Suppliers.objects.exclude(name="Internal").exclude(is_active=False)
        self.fields["project"].queryset=Projects.objects.exclude(is_active=False)
class NewProbeForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ("reagent", "supplier", "lot_no", "cond_rec", "date_rec", "po", "date_exp", "vol_rec")
        widgets = {"lot_no":forms.Textarea(attrs={"style": "height:2em;"}),
                   "date_rec":MySelectDateWidget(years=range(datetime.datetime.today().year-1,datetime.datetime.today().year+1)),
                   "date_exp":MySelectDateWidget(years=range(datetime.datetime.today().year-1,datetime.datetime.today().year+20)),
                   "reagent":forms.HiddenInput(),
                   "current_vol":forms.HiddenInput()}

    def clean(self):
        super(NewProbeForm, self).clean()
        if self.cleaned_data["date_exp"]<self.cleaned_data["date_rec"]:
            self.add_error("date_exp", forms.ValidationError("Expiry date occurs before received date"))
        elif self.cleaned_data["date_rec"]>datetime.date.today():
            self.add_error("date_rec", forms.ValidationError("Date received occurs in the future"))
    def __init__(self, *args, **kwargs):
        super(NewProbeForm, self).__init__(*args, **kwargs)
        self.fields["supplier"].queryset=Suppliers.objects.exclude(name="Internal").exclude(is_active=False)

class UseItemForm(forms.ModelForm):
    vol_used = forms.IntegerField(min_value=1, label=u"Volume Used (µl)")
    date_used = forms.DateField(widget=MySelectDateWidget(years=range(datetime.datetime.today().year-1,datetime.datetime.today().year+5)), label=u"Date Used")
    class Meta:
        model = Inventory
        fields = ("current_vol","date_op", "last_usage")
        widgets= {"current_vol":forms.HiddenInput,
                  "date_op":forms.HiddenInput,
                  "last_usage":forms.HiddenInput}
    def clean(self):
        super(UseItemForm, self).clean()
        if self.cleaned_data["vol_used"]>self.cleaned_data["current_vol"]:
            self.add_error("vol_used", forms.ValidationError("Volume Used Exceeds Current Volume in Tube"))
        if self.cleaned_data["date_used"]<self.cleaned_data["date_op"]:
            self.add_error("date_used", forms.ValidationError("Date Used is before Date Open"))
        if self.cleaned_data["last_usage"] is not None:
            if self.cleaned_data["date_used"]<self.cleaned_data["last_usage"].date:
                self.add_error("date_used", forms.ValidationError("This Usage Date is before the most recent use"))
        if self.cleaned_data["date_used"]>datetime.date.today():
            self.add_error("date_used", forms.ValidationError("Date of use occurs in the future"))

class OpenItemForm(forms.ModelForm):
    date_op = forms.DateField(widget=MySelectDateWidget(years=range(datetime.datetime.today().year-1,datetime.datetime.today().year+5)), label=u"Date Open")
    class Meta:
        model = Inventory
        fields = ("date_rec",)
        widgets = {"date_rec":forms.HiddenInput}
    def clean(self):
        super(OpenItemForm, self).clean()
        if self.cleaned_data["date_op"]<datetime.datetime.strptime(self.data["date_rec"],"%Y-%m-%d").date():
            self.add_error("date_op", forms.ValidationError("Date open occurs before received date"))
        elif self.cleaned_data["date_op"]>datetime.date.today():
            self.add_error("date_op", forms.ValidationError("Date open occurs in the future"))

class ValItemForm(forms.ModelForm):
    val_date = forms.DateField(widget=MySelectDateWidget(years=range(datetime.date.today().year-1,datetime.datetime.today().year+5)), label="Validation Date")
    val_run = forms.CharField(max_length=20, widget=forms.TextInput(attrs={"autocomplete": "off"}), label="Validation Run")
    class Meta:
        model = Inventory
        fields = ("date_op",)
        widgets=  {"date_op":forms.HiddenInput}
    def clean(self):
        super(ValItemForm, self).clean()
        if self.cleaned_data["val_date"]<datetime.datetime.strptime(self.data["date_op"],"%Y-%m-%d").date():
            self.add_error("val_date", forms.ValidationError("Date validated occurs before date opened"))
        elif self.cleaned_data["val_date"]>datetime.date.today():
            self.add_error("val_date", forms.ValidationError("Date of validation run occurs in the future"))

class FinishItemForm(forms.ModelForm):
    date_fin = forms.DateField(widget=MySelectDateWidget(years=range(datetime.datetime.today().year-1,datetime.datetime.today().year+5)), label=u"Date Finished")
    class Meta:
        model = Inventory
        fields = ("date_op","fin_text","is_op")
        widgets = {"date_op":forms.HiddenInput,
                   "is_op":forms.HiddenInput,
                   "fin_text":forms.Textarea(attrs={"style": "height:5em;"})}
    def clean(self):
        super(FinishItemForm, self).clean()
        if self.cleaned_data["is_op"]==True:
            if self.cleaned_data["date_fin"]<datetime.datetime.strptime(self.data["date_op"],"%Y-%m-%d").date():
                self.add_error("date_fin", forms.ValidationError("Date finished occurs before item was opened"))
        if self.cleaned_data["date_fin"]>datetime.date.today():
            self.add_error("date_fin", forms.ValidationError("Date of disposal occurs in the future"))

class NewSupForm(forms.ModelForm):
    class Meta:
        model = Suppliers
        fields = "__all__"
        widgets = {"is_active":forms.HiddenInput}
    def clean(self):
        super(NewSupForm, self).clean()
        if Suppliers.objects.filter(name=self.cleaned_data["name"]).exists():
            self.add_error("name", forms.ValidationError("A Supplier with the name {} already exists".format(self.cleaned_data["name"])))

class NewProjForm(forms.ModelForm):
    class Meta:
        model = Projects
        fields = "__all__"
        widgets = {"is_active":forms.HiddenInput}
    def clean(self):
        super(NewProjForm, self).clean()
        if Projects.objects.filter(name=self.cleaned_data["name"]).exists():
            self.add_error("name", forms.ValidationError("A Project with the name {} already exists".format(self.cleaned_data["name"])))


class NewReagentForm(forms.ModelForm):
    class Meta:
        model = Reagents
        fields= "__all__"
        ####UNHIDE STORAGE IF EVER USED
        widgets = {"count_no":forms.HiddenInput,
                   "recipe":forms.HiddenInput,
                   "supplier_def":Select2Widget,
                   "storage":forms.HiddenInput,
                   "is_active":forms.HiddenInput}
    def __init__(self, *args, **kwargs):
        super(NewReagentForm, self).__init__(*args, **kwargs)
        self.fields["supplier_def"].queryset=Suppliers.objects.exclude(name="Internal").exclude(is_active=False)

    def clean(self):
        super(NewReagentForm, self).clean()
        if Reagents.objects.filter(name=self.cleaned_data["name"]).exists():
            self.add_error("name", forms.ValidationError("A Reagent with the name {} already exists".format(self.cleaned_data["name"])))

class NewRecipeForm(forms.ModelForm):
    number=forms.IntegerField(min_value=1, label=u"Minimum Stock Level")
    class Meta:
        model = Recipe
        fields = "__all__"
        widgets = {"reagent":forms.HiddenInput,
                   "comp1":Select2Widget,
                   "comp2":Select2Widget,
                   "comp3":Select2Widget,
                   "comp4":Select2Widget,
                   "comp5":Select2Widget,
                   "comp6":Select2Widget,
                   "comp7":Select2Widget,
                   "comp8":Select2Widget,
                   "comp9":Select2Widget,
                   "comp10":Select2Widget}
        #Hides Mixes from Reagent lists
##    def __init__(self, *args, **kwargs):
##        super(NewRecipeForm, self).__init__(*args, **kwargs)
##        for i in range(1,11):
##            self.fields["comp{}".format(i)].queryset=Reagents.objects.filter(recipe_id=None)

    def clean(self):
        super(NewRecipeForm, self).clean()
        comps=[]
        errors=[]
        present=True
        reagents={}
        for k,v in self.cleaned_data.items():
            if "comp" in k:
                reagents[k]=v
##        reagents=self.cleaned_data
##        del(reagents["name"])
##        del(reagents["shelf_life"])
        for key, value in sorted(reagents.items(), key = lambda x:int(x[0][4:])):
            if "comp" in key:
                if value is not None:
                    if present==False:
                        errors+=[forms.ValidationError("There is a gap in selected reagents")]
                    if value.name in comps:
                        errors+=[forms.ValidationError("Reagent {} appears more than once".format(value.name))]
                    comps+=[value.name]
                else:
                    present=False
        if len(comps)<1:
            errors+=[forms.ValidationError("At least 1 component is needed to create a recipe")]
        if self.cleaned_data["shelf_life"]<1:
            self.add_error("shelf_life", forms.ValidationError("Shelf Life must be 1 month or more"))
        if errors:
            raise forms.ValidationError(errors)

class SearchForm(forms.Form):
    reagent=forms.CharField(label="Reagent Name", max_length=30, required=False)
    supplier=forms.CharField(label="Supplier Name", max_length=25, required=False)
    project=forms.ModelChoiceField(queryset = Projects.objects.order_by("name"), widget=Select2Widget, required=False)
    lot_no=forms.CharField(label="Lot Number", max_length=20, required=False)
    int_id=forms.CharField(label="Stock Number", max_length=4, required=False)
    in_stock=forms.ChoiceField(label="Include Finished Items?", choices=[(0,"NO"),(1,"YES")])

class ChangeDefForm1(forms.Form):
    name=forms.ModelChoiceField(queryset = Reagents.objects.filter(recipe_id=None).order_by("name"), widget=Select2Widget)

class ChangeDefForm(forms.Form):
    supplier_def=forms.ModelChoiceField(queryset = Suppliers.objects.all().exclude(name="Internal").exclude(is_active=False).order_by("name"), label=u"Select New Supplier", widget=Select2Widget)
    old=forms.ModelChoiceField(queryset = Suppliers.objects.all().order_by("name"), widget=forms.HiddenInput())
    def clean(self):
        super(ChangeDefForm, self).clean()
        if self.cleaned_data["old"]==self.cleaned_data["supplier_def"]:
            self.add_error("supplier_def", forms.ValidationError("Previous Supplier Selected. Item Not Changed"))

class RemoveSupForm(forms.Form):
    supplier=forms.ModelChoiceField(queryset = Suppliers.objects.all().exclude(name="Internal").order_by("name"), widget=Select2Widget)
    def clean(self):
        super(RemoveSupForm, self).clean()
        if len(Inventory.objects.filter(supplier_id=self.data["supplier"]))>0:
           self.add_error("supplier", forms.ValidationError("Unable to Delete Supplier. {} Inventory Items Exist With This Supplier".format(len(Inventory.objects.filter(supplier_id=self.data["supplier"])))))
           self.add_error("supplier", forms.ValidationError("If you no longer need this supplier try using the '(De)Activate Supplier' Page"))
        elif len(Reagents.objects.filter(supplier_def_id=self.data["supplier"]))>0:
            self.add_error("supplier", forms.ValidationError("Unable to Delete Supplier. The Following Items Have This Supplier as Their Default Supplier:"))
            for supplier in Reagents.objects.filter(supplier_def_id=self.data["supplier"]):
                self.add_error("supplier", forms.ValidationError(supplier))
            self.add_error("supplier", forms.ValidationError("If you no longer need this supplier try using the '(De)Activate Supplier' Page"))

class RemoveProjForm(forms.Form):
    project=forms.ModelChoiceField(queryset = Projects.objects.all().exclude(name="INTERNAL").order_by("name"), widget=Select2Widget)
    def clean(self):
        super(RemoveProjForm, self).clean()
        if len(Inventory.objects.filter(project_id=self.data["project"]))>0:
           self.add_error("project", forms.ValidationError("Unable to Delete Project. {} Inventory Items Exist With This Project".format(len(Inventory.objects.filter(project_id=self.data["project"])))))
           self.add_error("project", forms.ValidationError("If you no longer need this project try using the '(De)Activate Project' Page"))

class EditSupForm(forms.Form):
    name=forms.ModelChoiceField(queryset = Suppliers.objects.all().exclude(name="Internal").order_by("name"), widget=Select2Widget, label=u"Supplier")

    def clean(self):
        super(EditSupForm, self).clean()
        if len(Reagents.objects.filter(supplier_def=self.cleaned_data["name"]))>0 and Suppliers.objects.get(name=self.cleaned_data["name"]).is_active==True:
            self.add_error("name", forms.ValidationError("Unable to Deactivate Supplier: {}. The Following Items Have This Supplier as Their Default Supplier:".format(self.cleaned_data["name"])))
            for reagent in Reagents.objects.filter(supplier_def=self.data["name"]):
                self.add_error("name", forms.ValidationError(reagent))

class EditProjForm(forms.Form):
    name=forms.ModelChoiceField(queryset = Projects.objects.all().order_by("name"), widget=Select2Widget, label=u"Project")



class EditReagForm(forms.Form):
    name=forms.ModelChoiceField(queryset = Reagents.objects.all().order_by("name"), widget=Select2Widget, label=u"Reagent")

class EditInvForm(forms.Form):
    item=forms.CharField(label="Reagent Internal ID", max_length=4,widget=forms.TextInput(attrs={"autocomplete": "off"}))
    def clean(self):
        super(EditInvForm, self).clean()
        try:
            Inventory.objects.get(internal=Internal.objects.get(batch_number=self.cleaned_data["item"]))
        except:
            self.add_error("item", forms.ValidationError("Internal ID {} is not Linked to an Inventory Item".format(self.cleaned_data["item"])))

class DeleteForm(forms.Form):
    sure=forms.BooleanField(label="Tick this box and click save to proceed with the action")

class UnValForm(forms.Form):
    sure=forms.BooleanField(label="Tick this box and click save to proceed with the action")
    all_type=forms.ChoiceField(label="Remove validation for other items on this run?")

class ChangeMinForm1(forms.Form):
    name=forms.ModelChoiceField(queryset = Reagents.objects.all().order_by("name"), label="Reagent", widget=Select2Widget)

class ChangeMinForm(forms.Form):
    number=forms.IntegerField(min_value=0, label="New Minimum Stock Amount")
    old=forms.IntegerField(min_value=0, widget=forms.HiddenInput())
    def clean(self):
        super(ChangeMinForm, self).clean()
        if int(self.cleaned_data["old"])==int(self.cleaned_data["number"]):
            self.add_error("number", forms.ValidationError("This is the same as the Current Minimum Stock Level"))

class StockReportForm(forms.Form):
    name=forms.ModelChoiceField(queryset = Reagents.objects.filter(count_no__gte=1).order_by("name"), label="Reagent", widget=Select2Widget)

class ProjReportForm(forms.Form):
    name=forms.ModelChoiceField(queryset = Projects.objects.order_by("name"), label="Project", widget=Select2Widget)
    in_stock=forms.ChoiceField(label="Include Finished Items?", choices=[(0,"NO"),(1,"YES")])

class InvReportForm(forms.Form):
    report=forms.ChoiceField(label="Select Report To Generate",
                             choices=[("unval","All Unvalidated Items"),
                                      ("val","All Validated Items"),
                                      ("exp","Items Expiring Soon"),
                                      ("all","All In-Stock Items"),
                                      ("allinc","All In-Stock Items (Including Open Items)"),
                                      ("minstock","All Items Below Minimum Stock Level")])
    def clean(self):
        super(InvReportForm, self).clean()
        if self.cleaned_data["report"]=="minstock":
            queryset=Reagents.objects.filter(count_no__lt=F("min_count"))
            if len(queryset)==0:
                self.add_error("report", forms.ValidationError("There are no items with stock levels below their minimum"))

class PWResetForm(forms.Form):
    user = forms.CharField(label="Enter Username", max_length=20, widget=forms.TextInput(attrs={"autocomplete": "off"}))
    def clean(self):
        super(PWResetForm, self).clean()
        try:
            USER=User.objects.get(username=self.cleaned_data["user"])
            if USER.email=="":
                self.add_error("user", forms.ValidationError("User {} does not have an email address entered.\nContact an Admin to reset you password".format(self.cleaned_data["user"])))
        except:
            self.add_error("user", forms.ValidationError("Username {} does not exist".format(self.cleaned_data["user"])))

class WitnessForm(forms.Form):
    name=forms.ModelChoiceField(queryset = User.objects.filter(is_active=True).order_by("username"), widget=Select2Widget, label=u"Select Witness")
